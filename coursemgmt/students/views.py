from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.http import HttpResponse
import pandas as pd

from batches.models import Enrollment
from assessments.models import AssessmentResult
from certificates.models import Certificate
from training_management.access import CrudFormMixin, RoleRequiredMixin, role_required, has_role

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


@role_required("Admin", "Student")
def assessment_results(request):
    if has_role(request.user, "Student"):
        student = resolve_student(request.user)
        if not student:
            return render(request, "students/assessment_results.html", {"results": []})
        results = AssessmentResult.objects.filter(enrollment__student=student).select_related(
            "enrollment__batch__program",
            "assessment__course",
        ).order_by("-graded_at")
    else:
        student_id = request.GET.get("student")
        batch_id = request.GET.get("batch")
        program_id = request.GET.get("program")
        
        results = AssessmentResult.objects.select_related(
            "enrollment__batch__program",
            "assessment__course",
            "enrollment__student",
        )
        
        if student_id:
            results = results.filter(enrollment__student_id=student_id)
        if batch_id:
            results = results.filter(enrollment__batch_id=batch_id)
        if program_id:
            results = results.filter(enrollment__batch__program_id=program_id)
        
        results = results.order_by("-graded_at")
        student = Student.objects.filter(pk=student_id).first() if student_id else None
    
    context = {
        "results": results,
        "students": Student.objects.all() if not has_role(request.user, "Student") else [],
        "batches": Enrollment.objects.values_list("batch_id", flat=True).distinct() if not has_role(request.user, "Student") else [],
    }
    return render(request, "students/assessment_results.html", context)


@role_required("Admin")
def export_marks(request):
    export_type = request.GET.get("type", "all")
    student_id = request.GET.get("student")
    batch_id = request.GET.get("batch")
    program_id = request.GET.get("program")
    
    results = AssessmentResult.objects.select_related(
        "enrollment__batch__program",
        "enrollment__student",
        "assessment__course",
    )
    
    if export_type == "student" and student_id:
        results = results.filter(enrollment__student_id=student_id)
        filename = f"marks_student_{student_id}.xlsx"
    elif export_type == "batch" and batch_id:
        results = results.filter(enrollment__batch_id=batch_id)
        filename = f"marks_batch_{batch_id}.xlsx"
    elif export_type == "program" and program_id:
        results = results.filter(enrollment__batch__program_id=program_id)
        filename = f"marks_program_{program_id}.xlsx"
    else:
        filename = "marks_all.xlsx"
    
    data = []
    for result in results.order_by("enrollment__batch", "enrollment__student", "assessment__course"):
        data.append({
            "Student Name": result.enrollment.student.full_name,
            "Student Code": result.enrollment.student.student_code,
            "Batch": result.enrollment.batch.batch_name,
            "Program": result.enrollment.batch.program.program_name,
            "Course": result.assessment.course.course_name,
            "Assessment": result.assessment.assessment_name,
            "Marks Obtained": float(result.marks_obtained),
            "Total Marks": result.assessment.total_marks,
            "Status": result.status,
            "Graded Date": result.graded_at.strftime("%Y-%m-%d %H:%M") if result.graded_at else "Not Graded",
        })
    
    if not data:
        return render(request, "students/export_marks.html", {"error": "No assessment results found for export."})
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Assessment Results", index=False)
    
    return response


student_list = StudentListView.as_view()
student_detail = StudentDetailView.as_view()
student_create = StudentCreateView.as_view()
student_update = StudentUpdateView.as_view()
student_delete = StudentDeleteView.as_view()
student_guardian_create = StudentGuardianCreateView.as_view()
student_guardian_update = StudentGuardianUpdateView.as_view()
student_guardian_delete = StudentGuardianDeleteView.as_view()
