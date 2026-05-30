from django.db import models
from django.conf import settings


class Trainer(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
    ]
    
    trainer_id = models.AutoField(primary_key=True)
    trainer_code = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='trainer_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    joining_date = models.DateField(blank=True, null=True)
    experience = models.PositiveIntegerField(default=0, help_text="Experience in years")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    profile_photo = models.ImageField(upload_to='trainers/', blank=True, null=True)
    availability = models.CharField(max_length=50, default='Available')
    total_working_hours = models.PositiveIntegerField(default=0, help_text="Total training hours delivered")
    performance_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Average performance rating (0-5)")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.trainer_code} - {self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['-joining_date']


class Participant(models.Model):
    """Unmanaged model mapping to existing participants table."""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    batch_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'participants'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    id = models.AutoField(primary_key=True)
    participant_id = models.IntegerField()
    batch_id = models.IntegerField(blank=True, null=True)
    session_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance'
        ordering = ['-session_date']
        constraints = [
            models.UniqueConstraint(fields=['participant_id', 'session_date'], name='unique_attendance_per_session')
        ]
