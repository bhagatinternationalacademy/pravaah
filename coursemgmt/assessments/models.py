from django.db import models

from batches.models import Enrollment
from programs.models import Course


class Assessment(models.Model):
    assessment_id = models.BigAutoField(primary_key=True, db_column="assessment_id")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_column="course_id", related_name="assessments")
    assessment_name = models.CharField(max_length=150)
    assessment_type = models.CharField(max_length=60)
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assessments"
        ordering = ["-created_at", "assessment_name"]

    def __str__(self):
        return self.assessment_name


class AssessmentResult(models.Model):
    result_id = models.BigAutoField(primary_key=True, db_column="result_id")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, db_column="enrollment_id", related_name="assessment_results")
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, db_column="assessment_id", related_name="results")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="Pending")
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assessment_results"
        ordering = ["-submitted_at", "result_id"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "assessment"], name="uniq_enrollment_assessment")
        ]

    def __str__(self):
        return f"{self.enrollment} - {self.assessment}"
