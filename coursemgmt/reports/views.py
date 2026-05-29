from datetime import date
import csv

from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import render

from assessments.models import Assessment
from attendance.models import Attendance
from batches.models import Batch
from batches.models import Enrollment
from certificates.models import Certificate
from students.models import Student
from training_management.access import role_required
from trainers.models import Trainer


def _paginate(queryset, request, per_page=10):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _rows(page_obj, row_builder):
    return [row_builder(item) for item in page_obj.object_list]


@role_required("Admin", "Trainer", "Student")
def index(request):
    today = date.today()
    attendance_breakdown = list(
        Attendance.objects.values("status").annotate(total=Count("attendance_id")).order_by("status")
    )
    certificate_breakdown = [
        {"label": "Issued", "total": Certificate.objects.filter(issue_date__isnull=False).count()},
        {"label": "Pending", "total": Certificate.objects.filter(issue_date__isnull=True).count()},
    ]
    enrollment_months = list(
        Enrollment.objects.annotate(month=TruncMonth("enrollment_date"))
        .values("month")
        .annotate(total=Count("enrollment_id"))
        .order_by("month")
    )
    batch_breakdown = list(Batch.objects.values("status").annotate(total=Count("batch_id")).order_by("status"))
    attendance_total = Attendance.objects.count()
    attendance_present = Attendance.objects.filter(status__iexact="Present").count()
    certificate_total = Certificate.objects.count()
    certificate_issued = Certificate.objects.filter(issue_date__isnull=False).count()
    enrollment_total = Enrollment.objects.count()
    active_batches = Batch.objects.filter(status__iexact="Active").count()
    completed_batches = Batch.objects.filter(status__iexact="Completed").count()
    return render(
        request,
        "reports/index.html",
        {
            "students_count": Student.objects.count(),
            "trainers_count": Trainer.objects.count(),
            "attendance_count": attendance_total,
            "attendance_percentage": round((attendance_present / attendance_total) * 100, 1) if attendance_total else 0,
            "certificates_issued": certificate_issued,
            "certificate_success_rate": round((certificate_issued / certificate_total) * 100, 1) if certificate_total else 0,
            "assessments_count": Assessment.objects.count(),
            "batches_count": Batch.objects.count(),
            "active_batches": active_batches,
            "completed_batches": completed_batches,
            "batch_performance": round((completed_batches / Batch.objects.count()) * 100, 1) if Batch.objects.count() else 0,
            "enrollments_count": enrollment_total,
            "upcoming_batches": Batch.objects.filter(start_date__gte=today).count(),
            "attendance_labels": [row["status"] for row in attendance_breakdown],
            "attendance_counts": [row["total"] for row in attendance_breakdown],
            "certificate_labels": [row["label"] for row in certificate_breakdown],
            "certificate_counts": [row["total"] for row in certificate_breakdown],
            "enrollment_month_labels": [row["month"].strftime("%b %Y") if row["month"] else "-" for row in enrollment_months],
            "enrollment_month_counts": [row["total"] for row in enrollment_months],
            "batch_report_labels": [row["status"] for row in batch_breakdown],
            "batch_report_counts": [row["total"] for row in batch_breakdown],
        },
    )


@role_required("Admin", "Trainer", "Student")
def students_report(request):
    query = request.GET.get("q", "")
    queryset = Student.objects.select_related("course")
    if query:
        queryset = queryset.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(student_code__icontains=query))
    page = _paginate(queryset, request)
    return render(
        request,
        "reports/list.html",
        {
            "title": "Students Report",
            "page_obj": page,
            "rows": _rows(page, lambda s: {"title": s.full_name, "subtitle": s.student_code, "cells": [s.gender or "-", getattr(s.course, "course_name", "-"), s.status or "-"]}),
            "query": query,
            "status": None,
        },
    )


@role_required("Admin", "Trainer", "Student")
def trainers_report(request):
    query = request.GET.get("q", "")
    queryset = Trainer.objects.select_related("gender")
    if query:
        queryset = queryset.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(trainer_code__icontains=query))
    page = _paginate(queryset, request)
    return render(request, "reports/list.html", {"title": "Trainers Report", "page_obj": page, "rows": _rows(page, lambda t: {"title": t.full_name, "subtitle": t.trainer_code, "cells": [t.email, t.mobile, t.status]}), "query": query, "status": None})


@role_required("Admin", "Trainer", "Student")
def attendance_report(request):
    query = request.GET.get("q", "")
    queryset = Attendance.objects.select_related("enrollment__student", "enrollment__batch", "session")
    if query:
        queryset = queryset.filter(Q(enrollment__student__first_name__icontains=query) | Q(enrollment__student__last_name__icontains=query) | Q(status__icontains=query))
    page = _paginate(queryset, request)
    return render(request, "reports/list.html", {"title": "Attendance Report", "page_obj": page, "rows": _rows(page, lambda a: {"title": a.enrollment.student.full_name, "subtitle": a.enrollment.batch.batch_name, "cells": [a.session.session_topic, a.status, a.marked_at]}), "query": query, "status": None})


@role_required("Admin", "Trainer", "Student")
def certificates_report(request):
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    queryset = Certificate.objects.select_related("enrollment__student", "enrollment__batch")
    if query:
        queryset = queryset.filter(Q(certificate_no__icontains=query) | Q(verification_code__icontains=query))
    if status == "issued":
        queryset = queryset.filter(issue_date__isnull=False)
    elif status == "pending":
        queryset = queryset.filter(issue_date__isnull=True)
    page = _paginate(queryset, request)
    return render(request, "reports/list.html", {"title": "Certificates Report", "page_obj": page, "rows": _rows(page, lambda c: {"title": c.certificate_no, "subtitle": c.enrollment.student.full_name, "cells": [c.issue_date or "Not issued", c.expiry_date or "-", c.validity_status]}), "query": query, "status": status})


@role_required("Admin", "Trainer", "Student")
def assessments_report(request):
    query = request.GET.get("q", "")
    queryset = Assessment.objects.select_related("course")
    if query:
        queryset = queryset.filter(Q(assessment_name__icontains=query) | Q(course__course_name__icontains=query))
    page = _paginate(queryset, request)
    return render(request, "reports/list.html", {"title": "Assessments Report", "page_obj": page, "rows": _rows(page, lambda a: {"title": a.assessment_name, "subtitle": a.course.course_name, "cells": [a.assessment_type, a.total_marks, a.passing_marks]}), "query": query, "status": None})


@role_required("Admin", "Trainer", "Student")
def batches_report(request):
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    queryset = Batch.objects.select_related("program", "trainer")
    if query:
        queryset = queryset.filter(Q(batch_name__icontains=query) | Q(batch_code__icontains=query))
    if status:
        queryset = queryset.filter(status__iexact=status)
    page = _paginate(queryset, request)
    return render(request, "reports/list.html", {"title": "Batches Report", "page_obj": page, "rows": _rows(page, lambda b: {"title": b.batch_name, "subtitle": b.batch_code, "cells": [b.program.program_name, b.trainer.full_name if b.trainer else "-", f"{b.start_date} to {b.end_date}", b.status]}), "query": query, "status": status})


@role_required("Admin", "Trainer", "Student")
def export_csv(request, kind):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{kind}_report.csv"'
    writer = csv.writer(response)

    if kind == "attendance":
        writer.writerow(["Student", "Batch", "Session", "Status", "Marked At"])
        for item in Attendance.objects.select_related("enrollment__student", "enrollment__batch", "session"):
            writer.writerow([item.enrollment.student.full_name, item.enrollment.batch.batch_name, item.session.session_topic, item.status, item.marked_at])
    elif kind == "batches":
        writer.writerow(["Batch", "Code", "Program", "Trainer", "Start Date", "End Date", "Status"])
        for item in Batch.objects.select_related("program", "trainer"):
            writer.writerow([item.batch_name, item.batch_code, item.program.program_name, item.trainer.full_name if item.trainer else "-", item.start_date, item.end_date, item.status])
    elif kind == "assessments":
        writer.writerow(["Assessment", "Course", "Type", "Total Marks", "Passing Marks"])
        for item in Assessment.objects.select_related("course"):
            writer.writerow([item.assessment_name, item.course.course_name, item.assessment_type, item.total_marks, item.passing_marks])
    else:
        return HttpResponse("Invalid export type", status=400)
    return response
