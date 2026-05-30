from django.conf import settings
from django.db import models

from programs.models import Course
from training_management.codegen import generate_unique_code


class Student(models.Model):
    student_id = models.BigAutoField(primary_key=True, db_column="participant_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column="user_id", related_name="student_profile")
    student_code = models.CharField(max_length=64, unique=True, blank=True, db_column="admission_no")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, db_column="course_id", null=True, blank=True, related_name="participants")
    academic_year_id = models.IntegerField(null=True, blank=True)
    join_date = models.DateField(null=True, blank=True, db_column="created_at")
    status = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "participants"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if not self.student_code:
            self.student_code = generate_unique_code(Student, "student_code", "STD-")
        return super().save(*args, **kwargs)


class StudentGuardian(models.Model):
    guardian_id = models.BigAutoField(primary_key=True, db_column="guardian_id")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column="participant_id", related_name="guardians")
    guardian_name = models.CharField(max_length=200)
    relation = models.CharField(max_length=50, null=True, blank=True, db_column="relationship")
    mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    occupation = models.TextField(null=True, blank=True, db_column="address")

    class Meta:
        db_table = "participant_guardians"
        ordering = ["guardian_name"]

    def __str__(self):
        return f"{self.guardian_name} ({self.relation})"
