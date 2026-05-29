from decimal import Decimal

import pandas as pd
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import UserRole
from assessments.models import AssessmentResult
from certificates.models import Certificate
from students.models import Student
from trainers.models import Trainer
from training_management.access import role_required

from .forms import ExcelUploadForm


def _resolve_gender(value):
    from programs.models import Gender

    if pd.isna(value):
        return Gender.objects.first()
    return (
        Gender.objects.filter(gender_name__iexact=str(value)).first()
        or Gender.objects.filter(gender_code__iexact=str(value)).first()
        or Gender.objects.first()
    )


def _resolve_city(value):
    from programs.models import City

    if pd.isna(value):
        return City.objects.first()
    return (
        City.objects.filter(city_name__iexact=str(value)).first()
        or City.objects.filter(city_code__iexact=str(value)).first()
        or City.objects.first()
    )


def _resolve_course(data):
    from programs.models import Course

    for key in ("course_id", "course_code", "course_name", "course"):
        value = data.get(key)
        if pd.isna(value) or value in ("", None):
            continue
        if key == "course_id":
            try:
                return Course.objects.filter(course_id=int(value)).first()
            except (TypeError, ValueError):
                return None
        if key == "course_code":
            return Course.objects.filter(course_code__iexact=str(value).strip()).first()
        return Course.objects.filter(course_name__iexact=str(value).strip()).first()
    return None


def _parse_date(value):
    if pd.isna(value) or value in ("", None):
        return None
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass
    parsed = parse_date(str(value))
    if parsed:
        return parsed
    parsed_dt = parse_datetime(str(value))
    return parsed_dt.date() if parsed_dt else None


def _parse_decimal(value, default=0):
    if pd.isna(value) or value in ("", None):
        return Decimal(default)
    return Decimal(str(value))


@role_required("Admin")
def upload_excel(request):
    result = None
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            import_type = form.cleaned_data["import_type"]
            dataset = pd.read_excel(form.cleaned_data["file"])
            created = updated = invalid = 0
            errors = []

            with transaction.atomic():
                for index, row in dataset.iterrows():
                    data = row.to_dict()
                    try:
                        if import_type == "trainers":
                            gender = _resolve_gender(data.get("gender"))
                            obj, was_created = Trainer.objects.update_or_create(
                                trainer_code=str(data.get("trainer_code")).strip(),
                                defaults={
                                    "first_name": data.get("first_name", ""),
                                    "last_name": data.get("last_name", ""),
                                    "gender": gender,
                                    "dob": _parse_date(data.get("dob")),
                                    "qualification": data.get("qualification", ""),
                                    "mobile": str(data.get("mobile", "")),
                                    "email": data.get("email", ""),
                                    "join_date": _parse_date(data.get("join_date")) or _parse_date(data.get("dob")),
                                    "status": data.get("status", "Active"),
                                },
                            )
                        elif import_type == "students":
                            gender_value = data.get("gender")
                            gender = None if pd.isna(gender_value) else str(gender_value).strip()
                            course = _resolve_course(data)
                            obj, was_created = Student.objects.update_or_create(
                                student_code=str(data.get("student_code")).strip(),
                                defaults={
                                    "first_name": data.get("first_name", ""),
                                    "last_name": data.get("last_name", ""),
                                    "course": course,
                                    "gender": gender or None,
                                    "dob": _parse_date(data.get("dob")),
                                    "mobile": str(data.get("mobile", "")),
                                    "email": data.get("email", ""),
                                    "join_date": _parse_date(data.get("join_date")) or _parse_date(data.get("dob")),
                                    "status": data.get("status", "Active"),
                                },
                            )
                        elif import_type == "certificates":
                            obj, was_created = Certificate.objects.update_or_create(
                                certificate_no=str(data.get("certificate_no")).strip(),
                                defaults={
                                    "enrollment_id": int(data.get("enrollment_id")),
                                    "issue_date": _parse_date(data.get("issue_date")),
                                    "expiry_date": _parse_date(data.get("expiry_date")),
                                    "certificate_url": data.get("certificate_url", ""),
                                    "verification_code": str(data.get("verification_code")).strip(),
                                },
                            )
                        elif import_type == "assessment_results":
                            obj, was_created = AssessmentResult.objects.update_or_create(
                                enrollment_id=int(data.get("enrollment_id")),
                                assessment_id=int(data.get("assessment_id")),
                                defaults={
                                    "marks_obtained": _parse_decimal(data.get("marks_obtained")),
                                    "status": data.get("status", "Pending"),
                                    "submitted_at": _parse_datetime(data.get("submitted_at")),
                                    "graded_at": _parse_datetime(data.get("graded_at")),
                                },
                            )
                        else:
                            raise ValueError(f"Unsupported import type: {import_type}")
                        created += int(was_created)
                        updated += int(not was_created)
                    except Exception as exc:
                        invalid += 1
                        errors.append(f"Row {index + 2}: {exc}")
                        continue

            result = {
                "created": created,
                "updated": updated,
                "invalid": invalid,
                "errors": errors[:10],
            }
            messages.success(request, "Excel import completed.")
    else:
        form = ExcelUploadForm()

    return render(request, "uploads/upload.html", {"form": form, "result": result})


def _parse_datetime(value):
    if pd.isna(value) or value in ("", None):
        return None
    parsed = parse_datetime(str(value))
    return parsed
