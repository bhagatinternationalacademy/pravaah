from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from programs.models import Course, Program
from students.models import Student
from trainers.models import Trainer
from training_management.codegen import generate_batch_code, generate_unique_code


class Batch(models.Model):
    batch_id = models.BigAutoField(primary_key=True, db_column="batch_id")
    batch_code = models.CharField(max_length=30, unique=True, blank=True)
    batch_name = models.CharField(max_length=150)
    program = models.ForeignKey(Program, on_delete=models.PROTECT, db_column="program_id", related_name="batches")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, db_column="trainer_id", related_name="batches", null=True, blank=True)
    client_name = models.CharField(max_length=80, blank=True, default="")
    subject_short_name = models.CharField(max_length=40, blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    mode = models.CharField(max_length=30, default="Offline")
    status = models.CharField(max_length=20, default="Planned")

    class Meta:
        db_table = "batches"
        ordering = ["-start_date", "batch_name"]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})

    def __str__(self):
        return self.batch_name

    def save(self, *args, **kwargs):
        if not self.batch_code:
            program_initials = "".join(word[0] for word in self.program.program_name.split()[:3]).upper()[:3] or "BAT"
            client_code = "".join(word[0] for word in self.client_name.split()[:3]).upper()[:3] or "CLT"
            year = self.start_date.year if self.start_date else datetime.now().year
            subject_code = (self.subject_short_name or self.program.program_name.replace(" ", "")[:4]).upper()[:4] or "SUB"
            self.batch_code = generate_batch_code(Batch, program_initials, client_code, year, subject_code)
        return super().save(*args, **kwargs)

    @property
    def next_session(self):
        return self.sessions.order_by("session_date", "start_time").first()

    @property
    def schedule_count(self):
        return self.sessions.count()

    @property
    def participant_count(self):
        return self.enrollments.filter(status__iexact="Approved").count()

    @property
    def certificate_count(self):
        return self.enrollments.filter(certificates__issue_date__isnull=False).distinct().count()

    @property
    def pending_certificate_count(self):
        return self.enrollments.exclude(certificates__issue_date__isnull=False).distinct().count()

    @property
    def primary_course(self):
        latest_session = self.sessions.select_related("course").order_by("session_date", "start_time").first()
        if latest_session:
            return latest_session.course
        linked_course = self.program.program_courses.select_related("course").order_by("sequence_no", "id").first()
        return linked_course.course if linked_course else None


class Enrollment(models.Model):
    enrollment_id = models.BigAutoField(primary_key=True, db_column="enrollment_id")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, db_column="batch_id", related_name="enrollments")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, db_column="student_id", related_name="enrollments")
    enrollment_date = models.DateField()
    status = models.CharField(max_length=20, default="Pending")
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default="Pending")

    class Meta:
        db_table = "enrollments"
        ordering = ["-enrollment_date", "enrollment_id"]
        constraints = [
            models.UniqueConstraint(fields=["batch", "student"], name="uniq_batch_student")
        ]

    def __str__(self):
        return f"{self.student} - {self.batch}"


class Session(models.Model):
    session_id = models.BigAutoField(primary_key=True, db_column="session_id")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, db_column="batch_id", related_name="sessions")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, db_column="course_id", related_name="sessions")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, db_column="trainer_id", related_name="sessions")
    session_topic = models.CharField(max_length=200)
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    recording_url = models.URLField(blank=True)

    class Meta:
        db_table = "sessions"
        ordering = ["session_date", "start_time"]

    def clean(self):
        super().clean()
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after start time."})

        qs = Session.objects.filter(
            trainer=self.trainer,
            session_date=self.session_date,
        ).exclude(pk=self.pk)
        for item in qs:
            if self._overlaps(item.start_time, item.end_time):
                raise ValidationError({"trainer": "Trainer has an overlapping session."})

    def _overlaps(self, other_start, other_end):
        return self.start_time < other_end and self.end_time > other_start

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch} - {self.session_topic}"
