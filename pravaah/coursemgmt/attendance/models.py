from django.db import models

from batches.models import Enrollment, Session


class Attendance(models.Model):
    attendance_id = models.BigAutoField(primary_key=True, db_column="attendance_id")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, db_column="enrollment_id", related_name="attendance_records")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, db_column="session_id", related_name="attendance_records")
    status = models.CharField(max_length=20, default="Present")
    attendance_photo = models.ImageField(upload_to="attendance/", null=True, blank=True, db_column="attendance_photo")
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attendance"
        ordering = ["-marked_at"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "session"], name="uniq_enrollment_session_attendance")
        ]

    def __str__(self):
        return f"{self.enrollment} - {self.session} - {self.status}"
