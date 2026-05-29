from django.conf import settings
from django.db import models

from training_management.codegen import generate_unique_code

class CourseCategory(models.Model):
    category_id = models.BigAutoField(primary_key=True, db_column="category_id")
    category_code = models.CharField(max_length=20, unique=True)
    category_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "course_categories"
        ordering = ["category_name"]

    def __str__(self):
        return self.category_name


class AcademicYear(models.Model):
    academic_year_id = models.BigAutoField(primary_key=True, db_column="academic_year_id")
    academic_year = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "academic_years"
        ordering = ["-start_date"]

    def __str__(self):
        return self.academic_year


class RoomType(models.Model):
    room_type_id = models.BigAutoField(primary_key=True, db_column="room_type_id")
    room_type_code = models.CharField(max_length=20, unique=True)
    room_type_name = models.CharField(max_length=120)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "room_types"
        ordering = ["room_type_name"]

    def __str__(self):
        return self.room_type_name


class Gender(models.Model):
    gender_id = models.BigAutoField(primary_key=True, db_column="gender_id")
    gender_code = models.CharField(max_length=20, unique=True)
    gender_name = models.CharField(max_length=40)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "genders"
        ordering = ["gender_name"]

    def __str__(self):
        return self.gender_name


class StatusMaster(models.Model):
    status_master_id = models.BigAutoField(primary_key=True, db_column="status_master_id")
    entity_name = models.CharField(max_length=80)
    status_code = models.CharField(max_length=40)
    status_name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "status_master"
        ordering = ["entity_name", "status_name"]

    def __str__(self):
        return f"{self.entity_name} - {self.status_name}"


class City(models.Model):
    city_id = models.BigAutoField(primary_key=True, db_column="city_id")
    city_code = models.CharField(max_length=20, unique=True)
    city_name = models.CharField(max_length=120)
    state_name = models.CharField(max_length=120, blank=True)
    country_name = models.CharField(max_length=120, default="India")
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "cities"
        ordering = ["city_name"]

    def __str__(self):
        return self.city_name


class Program(models.Model):
    program_id = models.BigAutoField(primary_key=True, db_column="program_id")
    program_code = models.CharField(max_length=30, unique=True, blank=True)
    program_name = models.CharField(max_length=150)
    category = models.ForeignKey(CourseCategory, on_delete=models.PROTECT, db_column="category_id", related_name="programs")
    program_image = models.ImageField(upload_to="programs/", null=True, blank=True, db_column="program_image")
    description = models.TextField(blank=True)
    duration_days = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "programs"
        ordering = ["program_name"]

    def __str__(self):
        return self.program_name

    def save(self, *args, **kwargs):
        if not self.program_code:
            self.program_code = generate_unique_code(Program, "program_code", "PRG-")
        return super().save(*args, **kwargs)


class Course(models.Model):
    course_id = models.BigAutoField(primary_key=True, db_column="course_id")
    course_code = models.CharField(max_length=30, unique=True, blank=True)
    course_name = models.CharField(max_length=150)
    course_image = models.ImageField(upload_to="courses/", null=True, blank=True, db_column="course_image")
    description = models.TextField(blank=True)
    duration_hours = models.PositiveIntegerField(default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    level = models.CharField(max_length=30, default="Beginner")
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "courses_tcm"
        ordering = ["course_name"]

    def __str__(self):
        return self.course_name

    def save(self, *args, **kwargs):
        if not self.course_code:
            self.course_code = generate_unique_code(Course, "course_code", "CRS-")
        return super().save(*args, **kwargs)


class ProgramCourse(models.Model):
    id = models.BigAutoField(primary_key=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, db_column="program_id", related_name="program_courses")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", related_name="course_program_links")
    sequence_no = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "program_courses"
        ordering = ["sequence_no", "id"]
        constraints = [
            models.UniqueConstraint(fields=["program", "course"], name="uniq_program_course")
        ]

    def __str__(self):
        return f"{self.program} -> {self.course}"


class Module(models.Model):
    module_id = models.BigAutoField(primary_key=True, db_column="module_id")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", related_name="modules")
    module_name = models.CharField(max_length=150)
    module_image = models.ImageField(upload_to="modules/", null=True, blank=True, db_column="module_image")
    description = models.TextField(blank=True)
    sequence_no = models.PositiveIntegerField(default=1)
    duration_hours = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "modules"
        ordering = ["sequence_no", "module_name"]
        constraints = [
            models.UniqueConstraint(fields=["course", "module_name"], name="uniq_course_module")
        ]

    def __str__(self):
        return self.module_name


class Material(models.Model):
    material_id = models.BigAutoField(primary_key=True, db_column="material_id")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, db_column="module_id", related_name="materials")
    title = models.CharField(max_length=150)
    file_type = models.CharField(max_length=40)
    file_url = models.FileField(upload_to="materials/", db_column="file_url")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column="uploaded_by", related_name="uploaded_materials")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "materials"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title
