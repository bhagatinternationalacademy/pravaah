from django.db import models
from pravaah.trainers.models import Trainer


class Certification(models.Model):
    certification_id = models.AutoField(primary_key=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    certification_name = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)

    def status(self):
        from django.utils import timezone
        if not self.expiry_date:
            return 'Active'
        today = timezone.now().date()
        if self.expiry_date < today:
            return 'Expired'
        delta = (self.expiry_date - today).days
        if delta <= 30:
            return 'Expiring Soon'
        return 'Active'

    def __str__(self):
        return f"{self.certification_name} ({self.trainer})"

