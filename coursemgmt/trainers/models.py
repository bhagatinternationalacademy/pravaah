from django.conf import settings
from django.db import models

from programs.models import Gender, Program, Course
from training_management.codegen import generate_unique_code


class Trainer(models.Model):
    trainer_id = models.BigAutoField(primary_key=True, db_column="trainer_id")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="trainer_profile", db_column="user_id")
    trainer_code = models.CharField(max_length=30, unique=True, blank=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    gender = models.ForeignKey(Gender, on_delete=models.PROTECT, db_column="gender", related_name="trainers", null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=150, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    join_date = models.DateField(null=True, blank=True, db_column="joining_date")
    status = models.CharField(max_length=20, default="Active")
    availability = models.CharField(max_length=20, default="Available")

    class Meta:
        db_table = "trainers_trainer"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if not self.trainer_code:
            self.trainer_code = generate_unique_code(Trainer, "trainer_code", "TRN-")
        return super().save(*args, **kwargs)


class TrainerSkill(models.Model):
    id = models.BigAutoField(primary_key=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, db_column="trainer_id", related_name="skills")
    skill_id = models.PositiveIntegerField()
    proficiency_level = models.CharField(max_length=50)

    class Meta:
        db_table = "trainer_skills"
        ordering = ["trainer_id", "skill_id"]
        constraints = [
            models.UniqueConstraint(fields=["trainer", "skill_id"], name="uniq_trainer_skill")
        ]

    def __str__(self):
        return f"{self.trainer} - {self.skill_id}"


class Certification(models.Model):
    certification_id = models.BigAutoField(primary_key=True, db_column="certification_id")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, db_column="trainer_id", related_name="certifications")
    certification_name = models.CharField(max_length=150)
    issuing_authority = models.CharField(max_length=150, blank=True)
    certificate_no = models.CharField(max_length=80, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "certifications"
        ordering = ["-issue_date", "certification_name"]

    def __str__(self):
        return self.certification_name


class ProgramTrainer(models.Model):
    id = models.BigAutoField(primary_key=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, db_column="trainer_id", related_name="program_assignments")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, db_column="program_id", related_name="trainer_assignments")
    specialization = models.CharField(max_length=200, blank=True, help_text="Area of specialization for this program")
    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "program_trainers"
        ordering = ["program", "trainer"]
        constraints = [
            models.UniqueConstraint(fields=["trainer", "program"], name="uniq_trainer_program")
        ]

    def __str__(self):
        return f"{self.trainer.full_name} -> {self.program.program_name}"


class CourseTrainer(models.Model):
    id = models.BigAutoField(primary_key=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, db_column="trainer_id", related_name="course_assignments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", related_name="trainer_assignments")
    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "course_trainers"
        ordering = ["course", "trainer"]
        constraints = [
            models.UniqueConstraint(fields=["trainer", "course"], name="uniq_trainer_course")
        ]

    def __str__(self):
        return f"{self.trainer.full_name} -> {self.course.course_name}"
