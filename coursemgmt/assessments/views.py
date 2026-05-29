import csv

from django.http import HttpResponse
from django.db.models import F, FloatField, Q, Value, ExpressionWrapper
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from training_management.access import CrudFormMixin, RoleRequiredMixin, role_required

from batches.models import Batch

from .forms import AssessmentForm, AssessmentResultForm
from .models import Assessment, AssessmentResult


class AssessmentListView(RoleRequiredMixin, ListView):
    model = Assessment
    template_name = "assessments/list.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        qs = Assessment.objects.select_related("course")
        query = self.request.GET.get("q", "")
        if query:
            qs = qs.filter(Q(assessment_name__icontains=query) | Q(course__course_name__icontains=query) | Q(assessment_type__icontains=query))
        return qs


class AssessmentCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "shared/form.html"
    roles = ("Admin",)
    success_url = reverse_lazy("assessments:list")
    title = "Create Assessment"
    button_text = "Create"
    back_url = reverse_lazy("assessments:list")


class AssessmentUpdateView(AssessmentCreateView, UpdateView):
    title = "Edit Assessment"
    button_text = "Update"


class AssessmentDeleteView(RoleRequiredMixin, DeleteView):
    model = Assessment
    template_name = "shared/confirm_delete.html"
    roles = ("Admin",)
    success_url = reverse_lazy("assessments:list")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("assessments:list")
        return kwargs


class ResultListView(RoleRequiredMixin, ListView):
    model = AssessmentResult
    template_name = "assessments/results.html"
    paginate_by = 10
    roles = ("Admin", "Trainer", "Student")

    def get_queryset(self):
        qs = _results_queryset(self.request)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.request.GET.get("q", ""),
                "batch_id": self.request.GET.get("batch", ""),
                "status": self.request.GET.get("status", ""),
                "assessment_id": self.request.GET.get("assessment", ""),
                "batches": Batch.objects.select_related("program").order_by("batch_name"),
                "assessments": Assessment.objects.select_related("course").order_by("assessment_name"),
                "total_results": self.object_list.count(),
                "total_students": self.object_list.values("enrollment_id").distinct().count(),
                "passed_count": self.object_list.filter(status__iexact="Pass").count(),
            }
        )
        return context


class ResultCreateView(CrudFormMixin, RoleRequiredMixin, CreateView):
    model = AssessmentResult
    form_class = AssessmentResultForm
    template_name = "shared/form.html"
    roles = ("Admin", "Trainer")
    success_url = reverse_lazy("assessments:results")
    title = "Create Result"
    button_text = "Create"
    back_url = reverse_lazy("assessments:results")


class ResultUpdateView(ResultCreateView, UpdateView):
    title = "Edit Result"
    button_text = "Update"


class ResultDeleteView(RoleRequiredMixin, DeleteView):
    model = AssessmentResult
    template_name = "shared/confirm_delete.html"
    roles = ("Admin", "Trainer")
    success_url = reverse_lazy("assessments:results")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["back_url"] = reverse_lazy("assessments:results")
        return kwargs


def _results_queryset(request):
    qs = AssessmentResult.objects.select_related(
        "enrollment__student",
        "enrollment__batch__program",
        "assessment__course",
    )
    query = request.GET.get("q", "")
    batch_id = request.GET.get("batch", "")
    status = request.GET.get("status", "")
    assessment_id = request.GET.get("assessment", "")
    if query:
        qs = qs.filter(
            Q(enrollment__student__first_name__icontains=query)
            | Q(enrollment__student__last_name__icontains=query)
            | Q(enrollment__student__student_code__icontains=query)
            | Q(enrollment__batch__batch_name__icontains=query)
            | Q(enrollment__batch__batch_code__icontains=query)
            | Q(assessment__assessment_name__icontains=query)
            | Q(status__icontains=query)
        )
    if batch_id:
        qs = qs.filter(enrollment__batch_id=batch_id)
    if assessment_id:
        qs = qs.filter(assessment_id=assessment_id)
    if status:
        qs = qs.filter(status__iexact=status)
    return qs.annotate(
        percentage=ExpressionWrapper(
            F("marks_obtained") * Value(100.0) / F("assessment__total_marks"),
            output_field=FloatField(),
        )
    )


@role_required("Admin", "Trainer", "Student")
def assessment_list(request):
    return AssessmentListView.as_view()(request)


@role_required("Admin", "Trainer", "Student")
def result_list(request):
    return ResultListView.as_view()(request)


@role_required("Admin", "Trainer", "Student")
def result_export(request, kind):
    queryset = _results_queryset(request)

    if kind == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="assessment_results.csv"'
        writer = csv.writer(response)
        writer.writerow(["Student", "Student Code", "Batch", "Program", "Course", "Assessment", "Marks", "Total", "Status", "Submitted At", "Graded At"])
        for item in queryset:
            writer.writerow([
                item.enrollment.student.full_name,
                item.enrollment.student.student_code,
                item.enrollment.batch.batch_name,
                item.enrollment.batch.program.program_name,
                item.assessment.course.course_name,
                item.assessment.assessment_name,
                item.marks_obtained,
                item.assessment.total_marks,
                item.status,
                item.submitted_at,
                item.graded_at,
            ])
        return response

    if kind == "excel":
        try:
            from openpyxl import Workbook
        except Exception as exc:
            return HttpResponse(f"Excel export unavailable: {exc}", status=500)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Assessment Results"
        sheet.append(["Student", "Student Code", "Batch", "Program", "Course", "Assessment", "Marks", "Total", "Status", "Submitted At", "Graded At"])
        for item in queryset:
            sheet.append([
                item.enrollment.student.full_name,
                item.enrollment.student.student_code,
                item.enrollment.batch.batch_name,
                item.enrollment.batch.program.program_name,
                item.assessment.course.course_name,
                item.assessment.assessment_name,
                item.marks_obtained,
                item.assessment.total_marks,
                item.status,
                str(item.submitted_at or ""),
                str(item.graded_at or ""),
            ])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="assessment_results.xlsx"'
        workbook.save(response)
        return response

    if kind == "pdf":
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.pdfgen import canvas
        except Exception as exc:
            return HttpResponse(f"PDF export unavailable: {exc}", status=500)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="assessment_results.pdf"'
        pdf = canvas.Canvas(response, pagesize=landscape(A4))
        width, height = landscape(A4)
        y = height - 40
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Assessment Results")
        y -= 22
        pdf.setFont("Helvetica", 8)
        headers = "Student | Batch | Program | Course | Assessment | Marks / Total | Status"
        pdf.drawString(40, y, headers)
        y -= 14
        for item in queryset:
            line = f"{item.enrollment.student.full_name} | {item.enrollment.batch.batch_name} | {item.enrollment.batch.program.program_name} | {item.assessment.course.course_name} | {item.assessment.assessment_name} | {item.marks_obtained}/{item.assessment.total_marks} | {item.status}"
            pdf.drawString(40, y, line[:140])
            y -= 12
            if y < 30:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 8)
        pdf.save()
        return response

    return HttpResponse("Invalid export type", status=400)


assessment_create = AssessmentCreateView.as_view()
assessment_update = AssessmentUpdateView.as_view()
assessment_delete = AssessmentDeleteView.as_view()
result_create = ResultCreateView.as_view()
result_update = ResultUpdateView.as_view()
result_delete = ResultDeleteView.as_view()
result_export_view = result_export
