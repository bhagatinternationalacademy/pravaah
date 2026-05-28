from django.db import models
from django.conf import settings


class Trainer(models.Model):
    trainer_id = models.AutoField(primary_key=True)
    trainer_code = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='trainer_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, default='Active')
    profile_photo = models.ImageField(upload_to='trainers/', blank=True, null=True)
    availability = models.CharField(max_length=50, default='Available')

    def __str__(self):
        return f"{self.trainer_code} - {self.first_name} {self.last_name}"
