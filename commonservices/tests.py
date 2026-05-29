from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta

from .models import EmailNotificationLog, CalendarEvent, Reminder, Document, Announcement
from .services import (
    send_email_notification,
    check_schedule_conflict,
    create_event,
    update_event,
    upload_document,
    validate_document
)

from django.test import override_settings

@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
class CommonServicesTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="test_user", 
            email="test@pravaah.org", 
            password="Password123",
            first_name="Test"
        )

    def test_email_notification_logging(self):
        """Test that sending email creates log entry in transaction status."""
        success = send_email_notification(
            module_name="TEST_MODULE",
            event_type="TEST_EVENT",
            recipient_email="recipient@test.com",
            subject="Test Subject",
            template_name="emails/user_management/verify_email_confirmation.html",
            context={"first_name": "Test", "username": "test_user"}
        )
        
        # Verify transaction log was created
        log = EmailNotificationLog.objects.get(recipient_email="recipient@test.com")
        self.assertEqual(log.module_name, "TEST_MODULE")
        self.assertEqual(log.event_type, "TEST_EVENT")
        self.assertEqual(log.subject, "Test Subject")
        self.assertIn(log.status, ["SENT", "FAILED"])

    def test_calendar_schedule_conflicts(self):
        """Test schedule conflict detection and creation rules."""
        now = timezone.now()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)
        
        # Create first event
        event1 = create_event(
            user=self.user,
            title="Meeting 1",
            start_time=start,
            end_time=end
        )
        self.assertEqual(event1.title, "Meeting 1")
        
        # Check conflict overlap detection
        self.assertTrue(check_schedule_conflict(self.user, start + timedelta(minutes=30), end + timedelta(minutes=30)))
        self.assertFalse(check_schedule_conflict(self.user, end + timedelta(minutes=5), end + timedelta(hours=1)))
        
        # Attempt to create conflicting event (should raise ValueError)
        with self.assertRaises(ValueError):
            create_event(
                user=self.user,
                title="Conflicting Meeting",
                start_time=start + timedelta(minutes=15),
                end_time=end
            )

    def test_document_validation_and_upload(self):
        """Test file types, size validators, and upload services."""
        # Standard mock PDF upload
        pdf_file = SimpleUploadedFile("test_document.pdf", b"pdf content", content_type="application/pdf")
        doc = upload_document(
            title="Test PDF Document",
            file=pdf_file,
            related_module="usermgmt",
            related_id=1
        )
        self.assertEqual(doc.title, "Test PDF Document")
        self.assertEqual(doc.file_type, "pdf")
        self.assertEqual(doc.related_module, "usermgmt")
        
        # Invalid extension (should raise ValidationError)
        invalid_file = SimpleUploadedFile("malware.exe", b"malicious code", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            upload_document(
                title="Malicious Executable",
                file=invalid_file,
                related_module="usermgmt",
                related_id=1
            )
