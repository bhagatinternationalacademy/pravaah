import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from batches.models import Batch
from batches.models import Enrollment, Session
from training_management.access import CrudFormMixin, RoleRequiredMixin, has_role, role_required

from .forms import AttendanceForm
from .models import Attendance


class AttendanceListView(RoleRequiredMixin, ListView):
    model = Attendance
    template_name = "attendance/list.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        records = Attendance.objects.select_related("enrollment__student", "enrollment__batch", "session")
        query = self.request.GET.get("q", "")
        status = self.request.GET.get("status", "")
        batch = self.request.GET.get("batch", "")
        if query:
            records = records.filter(
                Q(enrollment__student__first_name__icontains=query)
                | Q(enrollment__student__last_name__icontains=query)
                | Q(session__session_topic__icontains=query)
                | Q(status__icontains=query)
            )
        if status:
            records = records.filter(status__iexact=status)
        if batch:
            records = records.filter(enrollment__batch_id=batch)
        return records

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.request.GET.get("q", ""),
                "status": self.request.GET.get("status", ""),
                "batch": self.request.GET.get("batch", ""),
                "can_manage": has_role(self.request.user, "Admin", "Trainer"),
                "batches": list(Batch.objects.values_list("batch_id", "batch_name").order_by("batch_name")),
            }
        )
        return context


class AttendanceCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "shared/form.html"
    roles = ("Admin", "Trainer")
    success_url = reverse_lazy("attendance:list")
    title = "Mark Attendance"
    button_text = "Save"
    back_url = reverse_lazy("attendance:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["batch_id"] = self.request.GET.get("batch") or self.request.POST.get("batch")
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Attendance saved.")
        return super().form_valid(form)


class AttendanceUpdateView(AttendanceCreateView, UpdateView):
    title = "Edit Attendance"
    button_text = "Update"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not kwargs.get("batch_id") and self.object:
            kwargs["batch_id"] = self.object.enrollment.batch_id
        return kwargs


class AttendanceDeleteView(RoleRequiredMixin, DeleteView):
    model = Attendance
    template_name = "shared/confirm_delete.html"
    roles = ("Admin", "Trainer")
    success_url = reverse_lazy("attendance:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("attendance:list")
        kwargs["title"] = "Delete Attendance"
        return kwargs


@role_required("Admin", "Trainer")
def bulk_mark(request):
    batch_id = request.GET.get("batch") or request.POST.get("batch")
    session_id = request.GET.get("session") or request.POST.get("session")
    batch = Batch.objects.filter(pk=batch_id).first() if batch_id else None
    session = Session.objects.filter(pk=session_id).first() if session_id else None
    enrollments = Enrollment.objects.none()
    batch_sessions = Session.objects.none()
    if batch:
        enrollments = Enrollment.objects.filter(batch=batch, status__iexact="Approved").select_related("student").order_by("student__first_name", "student__last_name")
        batch_sessions = Session.objects.filter(batch=batch).select_related("trainer", "course").order_by("session_date", "start_time")
    existing = {}
    if session and batch:
        existing = {item.enrollment_id: item for item in Attendance.objects.filter(session=session, enrollment__batch=batch)}
    enrollment_rows = [
        {
            "enrollment": enrollment,
            "record": existing.get(enrollment.pk),
        }
        for enrollment in enrollments
    ]
    if request.method == "POST" and batch and session:
        photo = request.FILES.get("attendance_photo")
        marked_present = 0
        marked_absent = 0
        for enrollment in enrollments:
            status = "Present" if request.POST.get(f"attendance_{enrollment.pk}") else "Absent"
            record, _ = Attendance.objects.get_or_create(enrollment=enrollment, session=session, defaults={"status": status})
            record.status = status
            if photo:
                record.attendance_photo = photo
                try:
                    photo.seek(0)
                except Exception:
                    pass
            record.save()
            if status == "Present":
                marked_present += 1
            else:
                marked_absent += 1
        messages.success(request, f"Bulk attendance updated: {marked_present} present, {marked_absent} absent.")
        return render(request, "attendance/bulk_mark_done.html", {"batch": batch, "session": session})
    return render(
        request,
        "attendance/bulk_mark.html",
        {
            "batches": Batch.objects.all().select_related("program", "trainer"),
            "sessions": batch_sessions if batch else Session.objects.none(),
            "batch": batch,
            "session": session,
            "enrollments": enrollments,
            "existing": existing,
            "enrollment_rows": enrollment_rows,
            "present_count": sum(1 for record in existing.values() if record.status == "Present"),
            "absent_count": sum(1 for record in existing.values() if record.status == "Absent"),
        },
    )


@role_required("Admin", "Trainer")
def batch_sessions_api(request):
    batch_id = request.GET.get("batch")
    if not batch_id:
        return JsonResponse([], safe=False)
    sessions = Session.objects.filter(batch_id=batch_id).select_related("trainer", "course").order_by("session_date", "start_time")
    payload = [
        {
            "id": session.pk,
            "label": f"{session.session_date} • {session.session_topic} ({session.start_time} - {session.end_time})",
        }
        for session in sessions
    ]
    return JsonResponse(payload, safe=False)


@role_required("Admin", "Trainer")
def bulk_export(request, kind):
    batch_id = request.GET.get("batch")
    session_id = request.GET.get("session")
    batch = Batch.objects.filter(pk=batch_id).first() if batch_id else None
    session = Session.objects.filter(pk=session_id).first() if session_id else None
    queryset = Attendance.objects.select_related("enrollment__student", "enrollment__batch", "session")
    if batch:
        queryset = queryset.filter(enrollment__batch=batch)
    if session:
        queryset = queryset.filter(session=session)

    if kind == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="bulk_attendance.csv"'
        writer = csv.writer(response)
        writer.writerow(["Student", "Batch", "Session", "Status", "Marked At"])
        for item in queryset:
            writer.writerow([item.enrollment.student.full_name, item.enrollment.batch.batch_name, item.session.session_topic, item.status, item.marked_at])
        return response

    if kind == "excel":
        try:
            from openpyxl import Workbook
        except Exception as exc:
            return HttpResponse(f"Excel export unavailable: {exc}", status=500)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Attendance"
        sheet.append(["Student", "Batch", "Session", "Status", "Marked At"])
        for item in queryset:
            sheet.append([item.enrollment.student.full_name, item.enrollment.batch.batch_name, item.session.session_topic, item.status, str(item.marked_at)])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="bulk_attendance.xlsx"'
        workbook.save(response)
        return response

    if kind == "pdf":
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception as exc:
            return HttpResponse(f"PDF export unavailable: {exc}", status=500)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="bulk_attendance.pdf"'
        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 40
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, "Bulk Attendance Report")
        y -= 24
        pdf.setFont("Helvetica", 10)
        for item in queryset:
            line = f"{item.enrollment.student.full_name} | {item.enrollment.batch.batch_name} | {item.session.session_topic} | {item.status} | {item.marked_at}"
            pdf.drawString(40, y, line[:120])
            y -= 14
            if y < 40:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 10)
        pdf.save()
        return response

    return HttpResponse("Invalid export type", status=400)


attendance_list = AttendanceListView.as_view()
attendance_create = AttendanceCreateView.as_view()
attendance_update = AttendanceUpdateView.as_view()
attendance_delete = AttendanceDeleteView.as_view()
attendance_bulk_mark = bulk_mark
attendance_batch_sessions_api = batch_sessions_api
attendance_bulk_export = bulk_export
