from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from batches.models import Enrollment
from assessments.models import AssessmentResult
from certificates.models import Certificate
from training_management.access import CrudFormMixin, RoleRequiredMixin, role_required

from .forms import StudentForm, StudentGuardianForm
from .models import Student, StudentGuardian


def resolve_student(user):
    return Student.objects.filter(email=user.email).first() or Student.objects.filter(student_code=user.username).first()


class StudentListView(RoleRequiredMixin, ListView):
    model = Student
    template_name = "students/list.html"
    paginate_by = 10
    roles = ("Admin", "Student")

    def get_queryset(self):
        qs = Student.objects.select_related("gender", "city")
        q = self.request.GET.get("q", "")
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(student_code__icontains=q) | Q(email__icontains=q))
        return qs


class StudentDetailView(RoleRequiredMixin, DetailView):
    model = Student
    template_name = "students/detail.html"
    context_object_name = "student"
    roles = ("Admin", "Student")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["guardians"] = self.object.guardians.all()
        kwargs["enrollments"] = self.object.enrollments.select_related("batch", "batch__program").prefetch_related("assessment_results__assessment").all()
        kwargs["results"] = AssessmentResult.objects.select_related(
            "enrollment__batch__program",
            "assessment__course",
        ).filter(enrollment__student=self.object).order_by("enrollment__batch__batch_name", "assessment__assessment_name")
        kwargs["result_count"] = kwargs["results"].count()
        kwargs["average_marks"] = round(
            sum(float(result.marks_obtained) for result in kwargs["results"]) / kwargs["results"].count(),
            2,
        ) if kwargs["results"].count() else 0
        kwargs["certificates"] = Certificate.objects.filter(enrollment__student=self.object).select_related("enrollment", "enrollment__batch")
        return kwargs


class StudentCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("students:list")
    title = "Create Student"
    button_text = "Create"
    back_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Student created successfully.")
        return super().form_valid(form)


class StudentUpdateView(StudentCreateView, UpdateView):
    title = "Edit Student"
    button_text = "Update"

    def form_valid(self, form):
        messages.success(self.request, "Student updated successfully.")
        return super().form_valid(form)


class StudentDeleteView(RoleRequiredMixin, DeleteView):
    model = Student
    template_name = "students/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("students:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("students:detail", args=[self.object.pk])
        return kwargs

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Student deleted successfully.")
        return super().delete(request, *args, **kwargs)


class StudentGuardianCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = StudentGuardian
    form_class = StudentGuardianForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("students:list")
    title = "Add Guardian"
    button_text = "Save"
    back_url = reverse_lazy("students:list")

    def get_initial(self):
        initial = super().get_initial()
        student_id = self.request.GET.get("student")
        if student_id:
            initial["student"] = student_id
        return initial


class StudentGuardianUpdateView(StudentGuardianCreateView, UpdateView):
    pass


class StudentGuardianDeleteView(RoleRequiredMixin, DeleteView):
    model = StudentGuardian
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("students:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("students:list")
        return kwargs


@role_required("Admin", "Student")
def dashboard(request):
    student = resolve_student(request.user)
    enrollments = Enrollment.objects.filter(student=student).select_related("batch", "batch__program") if student else Enrollment.objects.none()
    results = AssessmentResult.objects.filter(enrollment__student=student).select_related("enrollment__batch", "assessment__course") if student else AssessmentResult.objects.none()
    return render(
        request,
        "students/dashboard.html",
        {
            "student": student,
            "enrollments": enrollments[:10],
            "certificates": Certificate.objects.filter(enrollment__student=student)[:10] if student else [],
            "results": results[:10],
            "result_count": results.count(),
        },
    )


student_list = StudentListView.as_view()
student_detail = StudentDetailView.as_view()
student_create = StudentCreateView.as_view()
student_update = StudentUpdateView.as_view()
student_delete = StudentDeleteView.as_view()
student_guardian_create = StudentGuardianCreateView.as_view()
student_guardian_update = StudentGuardianUpdateView.as_view()
student_guardian_delete = StudentGuardianDeleteView.as_view()
