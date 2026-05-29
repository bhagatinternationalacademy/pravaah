from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Custom Validators for Documents
ALLOWED_FILE_TYPES = ['pdf', 'docx', 'jpg', 'jpeg', 'png']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_file_type(file):
    """Ensures uploaded files fall strictly inside approved extensions."""
    if not file or not file.name:
        return
    extension = file.name.split('.')[-1].lower()
    if extension not in ALLOWED_FILE_TYPES:
        raise ValidationError(f'Unsupported file type: {extension}. Allowed types: {", ".join(ALLOWED_FILE_TYPES)}')

def validate_file_size(file):
    """Prevents database block storage overuse by setting a 10MB threshold."""
    if file and file.size > MAX_FILE_SIZE:
        raise ValidationError('File size exceeds 10 MB limit')


# 1. Email Notification Logs
class EmailNotificationLog(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    )

    module_name = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.recipient_email} - {self.subject} ({self.status})"


# 2. Calendar Event
class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


# 3. Session Reminder
class Reminder(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='reminders')
    reminder_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder for {self.event.title} at {self.reminder_time}"


# 4. Polymorphic/Generic Document Management
class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='documents/',
        validators=[validate_file_type, validate_file_size]
    )
    file_type = models.CharField(max_length=50)
    related_module = models.CharField(max_length=100)  # e.g., 'usermgmt', 'trainermgmt'
    related_id = models.IntegerField()                # ID of related entity
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# 5. Announcements
class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
