from django.db import models



class DashboardCard(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    total_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message[:50]


class ActivityLog(models.Model):
    user_name = models.CharField(max_length=100)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.action}"
# Create your models here.
