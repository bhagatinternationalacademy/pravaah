from django.db import models
from django.utils import timezone

from batches.models import Enrollment
from training_management.codegen import generate_unique_code


class Certificate(models.Model):
    certificate_id = models.BigAutoField(primary_key=True, db_column="certificate_id")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, db_column="enrollment_id", related_name="certificates")
    certificate_no = models.CharField(max_length=80, unique=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(blank=True)
    verification_code = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "certificates"
        ordering = ["-issue_date", "certificate_no"]

    def __str__(self):
        return self.certificate_no

    @property
    def is_issued(self):
        return bool(self.issue_date)

    @property
    def is_valid(self):
        return bool(self.issue_date) and (not self.expiry_date or self.expiry_date >= timezone.localdate())

    @property
    def validity_status(self):
        if not self.is_issued:
            return "Not Issued"
        return "Valid" if self.is_valid else "Expired"

    def save(self, *args, **kwargs):
        if not self.certificate_no:
            self.certificate_no = generate_unique_code(Certificate, "certificate_no", "CERT-")
        if not self.verification_code:
            self.verification_code = generate_unique_code(Certificate, "verification_code", "VER-")
        return super().save(*args, **kwargs)
