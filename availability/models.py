from django.db import models
from pravaah.trainers.models import Trainer


class Availability(models.Model):
    date = models.DateField()
    status = models.CharField(max_length=50)
    reason = models.TextField(blank=True, null=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='availability_entries')
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.trainer} - {self.date} ({self.status})'


class LeaveRequest(models.Model):
    date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    requested_at = models.DateTimeField(null=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    processed_at = models.DateTimeField(null=True)
    extra1 = models.TextField(blank=True, null=True)
    extra2 = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'LeaveRequest {self.trainer} - {self.date} ({self.status})'


class AvailableAvailability(models.Model):
    date = models.DateField()
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='available_entries')

    def __str__(self):
        return f'{self.trainer} - {self.date}'