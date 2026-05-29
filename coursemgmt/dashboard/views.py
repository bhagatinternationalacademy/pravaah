from datetime import date

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import UserRole
from assessments.models import Assessment
from batches.models import Batch, Enrollment, Session
from certificates.models import Certificate
from programs.models import Course, Program
from students.models import Student
from trainers.models import Trainer


def _resolve_trainer(user):
    return Trainer.objects.filter(email=user.email).first() or Trainer.objects.filter(trainer_code=user.username).first()


def _resolve_student(user):
    return Student.objects.filter(email=user.email).first() or Student.objects.filter(student_code=user.username).first()


def landing(request):
    today = date.today()
    programs = (
        Program.objects.select_related("category")
        .annotate(
            course_count=Count("program_courses", distinct=True),
            module_count=Count("program_courses__course__modules", distinct=True),
            material_count=Count("program_courses__course__modules__materials", distinct=True),
        )
        .order_by("program_name")[:6]
    )
    courses = (
        Course.objects.annotate(
            module_count=Count("modules", distinct=True),
            material_count=Count("modules__materials", distinct=True),
        )
        .order_by("course_name")[:6]
    )
    return render(
        request,
        "dashboard/landing.html",
        {
            "total_programs": Program.objects.count(),
            "total_courses": Course.objects.count(),
            "total_trainers": Trainer.objects.count(),
            "active_batches": Batch.objects.filter(status__iexact="Active").count(),
            "ongoing_sessions": Session.objects.filter(session_date=today).count(),
            "certificates_issued": Certificate.objects.filter(issue_date__isnull=False).count(),
            "programs": programs,
            "courses": courses,
        },
    )


@login_required
def index(request):
    roles = set(UserRole.objects.filter(user=request.user).values_list("role__role_name", flat=True))
    today = date.today()

    if "Trainer" in roles:
        trainer = _resolve_trainer(request.user)
        sessions = Session.objects.filter(trainer=trainer).select_related("batch", "course").order_by("session_date", "start_time")[:8] if trainer else []
        return render(
            request,
            "dashboard/trainer.html",
            {
                "trainer": trainer,
                "sessions": sessions,
                "upcoming_sessions": Session.objects.filter(trainer=trainer, session_date__gte=today).count() if trainer else 0,
                "active_batches": Batch.objects.filter(trainer=trainer).count() if trainer else 0,
            },
        )

    if "Student" in roles:
        student = _resolve_student(request.user)
        enrollments = Enrollment.objects.filter(student=student).select_related("batch", "batch__program") if student else Enrollment.objects.none()
        return render(
            request,
            "dashboard/student.html",
            {
                "student": student,
                "enrollments": enrollments[:8],
                "attendance_count": enrollments.count() if student else 0,
                "certificate_count": Certificate.objects.filter(enrollment__student=student).count() if student else 0,
            },
        )

    context = {
        "total_programs": Program.objects.count(),
        "total_courses": Course.objects.count(),
        "total_trainers": Trainer.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "pending_enrollments": Enrollment.objects.filter(status__iexact="Pending").count(),
        "active_batches": Batch.objects.filter(status__iexact="Active").count(),
        "upcoming_sessions": Session.objects.filter(session_date__gte=today).count(),
        "ongoing_sessions": Session.objects.filter(session_date=today).count(),
        "certificates_issued": Certificate.objects.filter(issue_date__isnull=False).count(),
        "ongoing_batches": Batch.objects.filter(start_date__lte=today, end_date__gte=today).count(),
        "total_students": Student.objects.count(),
        "total_assessments": Assessment.objects.count(),
        "recent_batches": Batch.objects.select_related("program", "trainer").order_by("-start_date")[:5],
        "recent_sessions": Session.objects.select_related("batch", "course", "trainer").order_by("-session_date", "-start_time")[:5],
        "batch_status_breakdown": list(Batch.objects.values("status").annotate(total=Count("batch_id")).order_by("status")),
        "course_level_breakdown": list(Course.objects.values("level").annotate(total=Count("course_id")).order_by("level")),
    }
    return render(request, "dashboard/admin.html", context)
