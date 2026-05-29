from django.db import models

from programs.models import City, Gender
from training_management.codegen import generate_unique_code


class Student(models.Model):
    student_id = models.BigAutoField(primary_key=True, db_column="student_id")
    student_code = models.CharField(max_length=30, unique=True, blank=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    gender = models.ForeignKey(Gender, on_delete=models.PROTECT, db_column="gender", related_name="students")
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, db_column="city_id", null=True, blank=True, related_name="students")
    join_date = models.DateField()
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "students"
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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column="student_id", related_name="guardians")
    guardian_name = models.CharField(max_length=150)
    relation = models.CharField(max_length=60)
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "student_guardians"
        ordering = ["guardian_name"]

    def __str__(self):
        return f"{self.guardian_name} ({self.relation})"
