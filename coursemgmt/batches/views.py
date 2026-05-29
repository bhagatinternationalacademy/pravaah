from datetime import datetime, timedelta, time
from django.db import transaction
from django.db.models import Count

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from attendance.models import Attendance
from certificates.models import Certificate
from programs.models import Course
from training_management.access import CrudFormMixin, RoleRequiredMixin, has_role, role_required
from trainers.models import Trainer
from students.models import Student

from .forms import BatchFormationForm, EnrollmentForm, EnrollmentRequestForm, SessionForm
from .models import Batch, Enrollment, Session


def _resolve_student(user):
    return Student.objects.filter(email=user.email).first() or Student.objects.filter(student_code=user.username).first()


def _sync_batch_participants(batch, students, course):
    selected_ids = {student.pk for student in students}
    fee_amount = course.fees if course else 0
    today = datetime.now().date()

    for enrollment in batch.enrollments.exclude(student_id__in=selected_ids):
        if enrollment.status != "Rejected":
            enrollment.status = "Rejected"
            enrollment.save(update_fields=["status"])

    for student in students:
        enrollment, created = Enrollment.objects.get_or_create(
            batch=batch,
            student=student,
            defaults={
                "enrollment_date": today,
                "status": "Approved",
                "fee_amount": fee_amount,
                "discount": 0,
                "payment_status": "Pending",
            },
        )
        if not created:
            updates = []
            if enrollment.status != "Approved":
                enrollment.status = "Approved"
                updates.append("status")
            if not enrollment.enrollment_date:
                enrollment.enrollment_date = today
                updates.append("enrollment_date")
            if enrollment.fee_amount != fee_amount:
                enrollment.fee_amount = fee_amount
                updates.append("fee_amount")
            if enrollment.payment_status != "Pending":
                enrollment.payment_status = "Pending"
                updates.append("payment_status")
            if updates:
                enrollment.save(update_fields=updates)


def _generate_session_plan(batch, course):
    if not course or batch.sessions.exists():
        return 0
    modules = list(course.modules.order_by("sequence_no", "module_name").prefetch_related("materials"))
    if not modules:
        modules = [None]
    session_date = batch.start_date
    created = 0
    for module in modules:
        if session_date > batch.end_date:
            break
        topic = module.module_name if module else f"Introduction - {course.course_name}"
        session, was_created = Session.objects.get_or_create(
            batch=batch,
            session_date=session_date,
            start_time=time(9, 0),
            defaults={
                "course": course,
                "trainer": batch.trainer,
                "session_topic": topic,
                "end_time": time(10, 30),
                "meeting_link": "",
                "notes": "",
                "recording_url": "",
            },
        )
        if was_created:
            created += 1
        session_date += timedelta(days=1)
    return created


def _selected_enrollment_ids(request):
    values = request.POST.getlist("selected_enrollments")
    return [int(value) for value in values if str(value).isdigit()]


class BatchListView(RoleRequiredMixin, ListView):
    model = Batch
    template_name = "batches/list.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        qs = Batch.objects.select_related("program", "trainer").prefetch_related("sessions", "enrollments")
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(Q(batch_name__icontains=q) | Q(batch_code__icontains=q) | Q(program__program_name__icontains=q))
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status__iexact=status)
        return qs


class BatchDetailView(RoleRequiredMixin, DetailView):
    model = Batch
    template_name = "batches/detail.html"
    context_object_name = "batch"
    roles = ("Admin", "Trainer", "Student")

    def get_context_data(self, **kwargs):
        from trainers.models import CourseTrainer
        kwargs = super().get_context_data(**kwargs)
        
        courses = []
        for session in self.object.sessions.select_related("course").distinct():
            trainers = CourseTrainer.objects.filter(course=session.course, is_active=True).select_related("trainer")
            courses.append({
                "course": session.course,
                "trainers": list(trainers),
            })
        
        kwargs["enrollments"] = self.object.enrollments.select_related("student").all()
        kwargs["sessions"] = self.object.sessions.select_related("course", "trainer").all()
        kwargs["courses"] = courses
        kwargs["attendance_stats"] = list(
            Attendance.objects.filter(enrollment__batch=self.object)
            .values("status")
            .annotate(total=Count("attendance_id"))
            .order_by("status")
        )
        kwargs["certificates"] = Certificate.objects.filter(enrollment__batch=self.object).select_related("enrollment__student")
        return kwargs


class BatchCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Batch
    form_class = BatchFormationForm
    template_name = "batches/formation.html"
    roles = ("Admin",)
    success_url = reverse_lazy("batches:list")
    title = "Create Batch"
    button_text = "Create Batch"
    back_url = reverse_lazy("batches:list")

    def get_success_url(self):
        return reverse_lazy("batches:detail", args=[self.object.pk])

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            _sync_batch_participants(self.object, form.cleaned_data.get("participants", []), form.cleaned_data.get("course"))
            if form.cleaned_data.get("generate_session_plan"):
                _generate_session_plan(self.object, form.cleaned_data.get("course") or self.object.primary_course)
        messages.success(self.request, "Batch created and participants assigned.")
        return HttpResponseRedirect(self.get_success_url())


class BatchUpdateView(BatchCreateView, UpdateView):
    title = "Edit Batch"
    button_text = "Update Batch"

    def get_success_url(self):
        return reverse_lazy("batches:detail", args=[self.object.pk])

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            _sync_batch_participants(self.object, form.cleaned_data.get("participants", []), form.cleaned_data.get("course") or self.object.primary_course)
            if form.cleaned_data.get("generate_session_plan") and not self.object.sessions.exists():
                _generate_session_plan(self.object, form.cleaned_data.get("course") or self.object.primary_course)
        messages.success(self.request, "Batch updated.")
        return HttpResponseRedirect(self.get_success_url())


class BatchDeleteView(RoleRequiredMixin, DeleteView):
    model = Batch
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("batches:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("batches:detail", args=[self.object.pk])
        return kwargs


class EnrollmentCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("batches:list")
    title = "Create Enrollment"
    button_text = "Create"
    back_url = reverse_lazy("batches:list")

    def get_initial(self):
        initial = super().get_initial()
        batch_id = self.request.GET.get("batch")
        if batch_id:
            initial["batch"] = batch_id
        return initial


class EnrollmentRequestView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentRequestForm
    template_name = "shared/form.html"
    roles = ("Student",)
    success_url = reverse_lazy("dashboard:index")
    title = "Request Enrollment"
    button_text = "Submit"
    back_url = reverse_lazy("landing")

    def get_initial(self):
        initial = super().get_initial()
        batch_id = self.request.GET.get("batch")
        if batch_id:
            initial["batch"] = batch_id
        student = _resolve_student(self.request.user)
        if student:
            initial["student"] = student.pk
        return initial

    def form_valid(self, form):
        form.instance.status = "Pending"
        form.instance.enrollment_date = form.instance.enrollment_date or datetime.now().date()
        form.instance.payment_status = "Pending"
        form.instance.fee_amount = form.instance.batch.program.program_courses.count() * 0
        messages.success(self.request, "Enrollment request submitted.")
        return super().form_valid(form)


class EnrollmentUpdateView(EnrollmentCreateView, UpdateView):
    pass


class EnrollmentDeleteView(RoleRequiredMixin, DeleteView):
    model = Enrollment
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("batches:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("batches:list")
        return kwargs


@role_required("Admin")
def enrollment_review(request):
    enrollments = Enrollment.objects.select_related("batch__program", "student").order_by("-enrollment_date", "-enrollment_id")
    batch_form = BatchFormationForm(prefix="batch")

    if request.method == "POST":
        action = request.POST.get("action")
        selected_ids = _selected_enrollment_ids(request)
        selected_qs = enrollments.filter(pk__in=selected_ids, status__iexact="Pending")

        if action in {"approve", "reject"}:
            new_status = "Approved" if action == "approve" else "Rejected"
            updated = selected_qs.update(status=new_status)
            messages.success(request, f"{updated} enrollment(s) {new_status.lower()}.")
            return HttpResponseRedirect(reverse_lazy("batches:enrollment-review"))

        if action == "create_batch":
            batch_form = BatchFormationForm(request.POST, prefix="batch")
            if not selected_ids:
                messages.error(request, "Select at least one applicant before creating a batch.")
            elif not batch_form.is_valid():
                messages.error(request, "Please fix the batch details and try again.")
            else:
                from django.db import transaction
                with transaction.atomic():
                    batch = batch_form.save()
                    selected_enrollments = list(selected_qs.select_related("student", "batch"))
                    if not selected_enrollments:
                        messages.error(request, "No pending applicants were selected.")
                        return HttpResponseRedirect(reverse_lazy("batches:enrollment-review"))
                    for enrollment in selected_enrollments:
                        enrollment.batch = batch
                        enrollment.status = "Approved"
                        enrollment.enrollment_date = enrollment.enrollment_date or datetime.now().date()
                        enrollment.payment_status = "Pending"
                        enrollment.fee_amount = batch.primary_course.fees if batch.primary_course else enrollment.fee_amount
                        enrollment.save()
                    if batch_form.cleaned_data.get("generate_session_plan"):
                        _generate_session_plan(batch, batch_form.cleaned_data.get("course") or batch.primary_course)
                messages.success(request, f"Batch {batch.batch_code} created with {len(selected_enrollments)} student(s).")
                return HttpResponseRedirect(reverse_lazy("batches:detail", args=[batch.pk]))

    return render(
        request,
        "batches/enrollment_review.html",
        {
            "pending": enrollments.filter(status__iexact="Pending"),
            "approved": enrollments.filter(status__iexact="Approved"),
            "rejected": enrollments.filter(status__iexact="Rejected"),
            "batch_form": batch_form,
        },
    )


@role_required("Admin")
def enrollment_action(request, pk, action):
    enrollment = Enrollment.objects.select_related("batch", "student").get(pk=pk)
    if action not in {"approve", "reject"}:
        raise ValueError("Invalid enrollment action")
    enrollment.status = "Approved" if action == "approve" else "Rejected"
    enrollment.save(update_fields=["status"])
    messages.success(request, f"Enrollment {enrollment.status.lower()}.")
    return render(request, "batches/enrollment_action_done.html", {"enrollment": enrollment})


class SessionCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Session
    form_class = SessionForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("batches:list")
    title = "Schedule Session"
    button_text = "Save"
    back_url = reverse_lazy("batches:list")

    def get_initial(self):
        initial = super().get_initial()
        batch_id = self.request.GET.get("batch")
        trainer_id = self.request.GET.get("trainer")
        course_id = self.request.GET.get("course")
        if batch_id:
            initial["batch"] = batch_id
        if trainer_id:
            initial["trainer"] = trainer_id
        if course_id:
            initial["course"] = course_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Session saved.")
        return super().form_valid(form)


class SessionUpdateView(SessionCreateView, UpdateView):
    pass


class SessionDeleteView(RoleRequiredMixin, DeleteView):
    model = Session
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("batches:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("batches:detail", args=[self.object.batch_id])
        return kwargs


@role_required("Admin")
def generate_session_plan(request, pk):
    batch = Batch.objects.select_related("program", "trainer").get(pk=pk)
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    course = batch.primary_course
    if not course:
        messages.error(request, "No course is linked to this batch yet.")
        return HttpResponseRedirect(reverse_lazy("batches:detail", args=[batch.pk]))
    created = _generate_session_plan(batch, course)
    if created:
        messages.success(request, f"Generated {created} session plan items.")
    else:
        messages.info(request, "Session plan already exists.")
    return HttpResponseRedirect(reverse_lazy("batches:detail", args=[batch.pk]))


@role_required("Admin")
def available_trainers(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    batch_id = request.GET.get("batch_id")
    trainers = Trainer.objects.filter(status__iexact="Active").order_by("first_name", "last_name")
    if start_date and end_date:
        conflicts = Session.objects.filter(session_date__range=(start_date, end_date)).values_list("trainer_id", flat=True)
        if batch_id:
            conflicts = Session.objects.filter(session_date__range=(start_date, end_date)).exclude(batch_id=batch_id).values_list("trainer_id", flat=True)
        trainers = trainers.exclude(pk__in=conflicts)
    payload = [{"id": trainer.pk, "name": trainer.full_name, "code": trainer.trainer_code} for trainer in trainers]
    return JsonResponse(payload, safe=False)


@role_required("Admin", "Trainer", "Student")
def calendar(request):
    return render(request, "batches/calendar.html", {"trainers": Trainer.objects.all(), "batches": Batch.objects.all(), "courses": Course.objects.all()})


@role_required("Admin", "Trainer", "Student")
def calendar_events(request):
    trainer_id = request.GET.get("trainer")
    batch_id = request.GET.get("batch")
    course_id = request.GET.get("course")
    sessions = Session.objects.select_related("batch", "course", "trainer")
    batches = Batch.objects.select_related("program", "trainer")
    if trainer_id:
        sessions = sessions.filter(trainer_id=trainer_id)
        batches = batches.filter(trainer_id=trainer_id)
    if batch_id:
        sessions = sessions.filter(batch_id=batch_id)
        batches = batches.filter(batch_id=batch_id)
    if course_id:
        sessions = sessions.filter(course_id=course_id)
    events = []
    for batch in batches:
        events.append(
            {
                "title": f"Batch: {batch.batch_name}",
                "start": batch.start_date.isoformat(),
                "end": (batch.end_date + timedelta(days=1)).isoformat(),
                "display": "background",
                "allDay": True,
                "backgroundColor": "#dbeafe",
                "borderColor": "#93c5fd",
                "extendedProps": {
                    "batch": batch.batch_name,
                    "program": batch.program.program_name,
                    "trainer": batch.trainer.full_name if batch.trainer else "",
                },
            }
        )
    for session in sessions:
        start = datetime.combine(session.session_date, session.start_time)
        end = datetime.combine(session.session_date, session.end_time)
        events.append({
            "id": session.pk,
            "title": f"{session.batch.batch_code} - {session.session_topic}",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "backgroundColor": "#1d4ed8",
            "borderColor": "#1d4ed8",
            "extendedProps": {"trainer": session.trainer.full_name, "batch": session.batch.batch_name, "course": session.course.course_name},
        })
    return JsonResponse(events, safe=False)


@role_required("Admin")
def session_move(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    session = Session.objects.get(pk=request.POST.get("id"))
    session.session_date = request.POST.get("date")
    session.start_time = request.POST.get("start")
    session.end_time = request.POST.get("end") or session.end_time
    session.save()
    return JsonResponse({"ok": True})


batch_list = BatchListView.as_view()
batch_detail = BatchDetailView.as_view()
batch_create = BatchCreateView.as_view()
batch_update = BatchUpdateView.as_view()
batch_delete = BatchDeleteView.as_view()
enrollment_create = EnrollmentCreateView.as_view()
enrollment_request = EnrollmentRequestView.as_view()
enrollment_update = EnrollmentUpdateView.as_view()
enrollment_delete = EnrollmentDeleteView.as_view()
enrollment_review_view = enrollment_review
enrollment_action_view = enrollment_action
session_create = SessionCreateView.as_view()
session_update = SessionUpdateView.as_view()
session_delete = SessionDeleteView.as_view()
session_move_view = session_move
