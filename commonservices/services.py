import uuid
import random
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone

from .models import (
    EmailNotificationLog,
    CalendarEvent,
    Reminder,
    Document,
    Announcement,
    validate_file_type,
    validate_file_size
)
from .utils import generate_otp as utils_generate_otp
from .constants import *

# ==========================================
# 1. Email Notification & Templating Services
# ==========================================

def render_email_template(template_name, context):
    """Safely renders HTML template utilizing provided dynamic context dictionary."""
    return render_to_string(template_name, context)

def send_email_notification(module_name, event_type, recipient_email, subject, template_name, context):
    """Sends email notification using SMTP configuration, and registers transaction logs."""
    email_log = EmailNotificationLog.objects.create(
        module_name=module_name,
        event_type=event_type,
        recipient_email=recipient_email,
        subject=subject,
        template_name=template_name,
        status='PENDING'
    )
    
    try:
        html_content = render_email_template(template_name, context)
        from_email = getattr(settings, 'EMAIL_HOST_USER', None)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body='',
            from_email=from_email,
            to=[recipient_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()
        return True
    except Exception as error:
        print(f"Error sending email: {error}")
        email_log.status = 'FAILED'
        email_log.error_message = str(error)
        email_log.save()
        return False

def generate_verification_token(user):
    """Creates a base64 encoded user primary key and a secure signature token."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token

def generate_otp():
    """Generates a random 6-digit OTP string."""
    return utils_generate_otp()


# ==========================================
# 2. User Management Notification Triggers
# ==========================================

def send_account_verification_email(user, host):
    """Generates a verification token and dispatches an account activation link email."""
    uidb64, token = generate_verification_token(user)
    verify_link = f"http://{host}/verify-email/{uidb64}/{token}/"
    
    return send_email_notification(
        module_name='USER_MANAGEMENT',
        event_type='ACCOUNT_VERIFICATION',
        recipient_email=user.email,
        subject=VERIFY_EMAIL_SUBJECT,
        template_name='emails/user_management/verify_email.html',
        context={
            'first_name': user.first_name,
            'username': user.username,
            'verify_link': verify_link,
        }
    )

def send_verification_confirmation_email(user):
    """Dispatches a confirmation email upon successful user account verification."""
    return send_email_notification(
        module_name='USER_MANAGEMENT',
        event_type='VERIFY_CONFIRMATION',
        recipient_email=user.email,
        subject=VERIFY_CONFIRMATION_SUBJECT,
        template_name='emails/user_management/verify_email_confirmation.html',
        context={
            'first_name': user.first_name,
            'username': user.username,
        }
    )

def send_password_reset_otp_email(user, reset_page_url):
    """Dispatches a random OTP code verification email for password recovery."""
    otp = generate_otp()
    send_email_notification(
        module_name='USER_MANAGEMENT',
        event_type='PASSWORD_RESET_OTP',
        recipient_email=user.email,
        subject=PASSWORD_RESET_OTP_SUBJECT,
        template_name='emails/user_management/password_reset_otp.html',
        context={
            'otp': otp,
            'expiry_minutes': OTP_EXPIRY_MINUTES,
            'reset_page_url': reset_page_url,
        }
    )
    return otp



# ==========================================
# -  Student Management Notification Triggers
# ==========================================
def send_student_registration_confirmation_email(user, host):
    """Dispatches a confirmation email upon successful student registration."""
    return send_email_notification(
        module_name='STUDENT_MANAGEMENT',
        event_type='REGISTRATION_SUCCESS',
        recipient_email=user.email,
        subject=REGISTRATION_SUCCESS_SUBJECT,
        template_name='emails/student_management/registration_confirmation.html',
        context={
            'first_name': user.first_name,
            'username': user.username,
        }
    )


# ==========================================
# 3. Trainer Management Notification Triggers
# ==========================================

def send_batch_assignment_notification(trainer, batch_name, start_date):
    """Alerts trainer on course batch assignments."""
    return send_email_notification(
        module_name='TRAINER_MANAGEMENT',
        event_type='BATCH_ASSIGNMENT',
        recipient_email=trainer.email,
        subject=BATCH_ASSIGNMENT_SUBJECT,
        template_name='emails/trainer_management/batch_assignment.html',
        context={
            'trainer_name': trainer.first_name or trainer.username,
            'batch_name': batch_name,
            'start_date': start_date,
        }
    )

def send_session_reminder_notification(trainer, session_name, session_time):
    """Dispatches warning notifications for upcoming trainer meetings."""
    return send_email_notification(
        module_name='TRAINER_MANAGEMENT',
        event_type='SESSION_REMINDER',
        recipient_email=trainer.email,
        subject=SESSION_REMINDER_SUBJECT,
        template_name='emails/trainer_management/session_reminder.html',
        context={
            'trainer_name': trainer.first_name or trainer.username,
            'session_name': session_name,
            'session_time': session_time,
        }
    )

def send_leave_status_notification(trainer, leave_status, reason):
    """Dispatches leave request outcome alerts to trainer."""
    subject = LEAVE_APPROVED_SUBJECT if leave_status == 'APPROVED' else LEAVE_REJECTED_SUBJECT
    return send_email_notification(
        module_name='TRAINER_MANAGEMENT',
        event_type='LEAVE_STATUS',
        recipient_email=trainer.email,
        subject=subject,
        template_name='emails/trainer_management/leave_request_status.html',
        context={
            'trainer_name': trainer.first_name or trainer.username,
            'leave_status': leave_status,
            'reason': reason,
        }
    )

def send_schedule_conflict_notification(trainer, conflict_message):
    """Dispatches alert of conflict overlay on session plans."""
    return send_email_notification(
        module_name='TRAINER_MANAGEMENT',
        event_type='SCHEDULE_CONFLICT',
        recipient_email=trainer.email,
        subject=SCHEDULE_CONFLICT_SUBJECT,
        template_name='emails/trainer_management/schedule_conflict.html',
        context={
            'trainer_name': trainer.first_name or trainer.username,
            'conflict_message': conflict_message,
        }
    )

def send_admin_announcement_notification(trainer, announcement_title, announcement_message):
    """Relays important admin announcements directly to trainer."""
    return send_email_notification(
        module_name='TRAINER_MANAGEMENT',
        event_type='ADMIN_ANNOUNCEMENT',
        recipient_email=trainer.email,
        subject=ADMIN_ANNOUNCEMENT_SUBJECT,
        template_name='emails/trainer_management/admin_announcement.html',
        context={
            'trainer_name': trainer.first_name or trainer.username,
            'announcement_title': announcement_title,
            'announcement_message': announcement_message,
        }
    )


# ==========================================
# 4. Training Course Management Notification Triggers
# ==========================================

def send_student_enrollment_notification(admin_email, student_name, batch_name):
    """Alerts administration on new student enrollments."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='STUDENT_ENROLLMENT',
        recipient_email=admin_email,
        subject=STUDENT_ENROLLMENT_RECEIVED_SUBJECT,
        template_name='emails/training_course_management/student_enrollment_received.html',
        context={
            'student_name': student_name,
            'batch_name': batch_name,
        }
    )

def send_enrollment_status_notification(student_email, student_name, batch_name, status):
    """Alerts students on validation outcome of their enrollment requests."""
    subject = ENROLLMENT_APPROVED_SUBJECT if status == 'APPROVED' else ENROLLMENT_REJECTED_SUBJECT
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='ENROLLMENT_STATUS',
        recipient_email=student_email,
        subject=subject,
        template_name='emails/training_course_management/enrollment_status.html',
        context={
            'student_name': student_name,
            'batch_name': batch_name,
            'status': status,
        }
    )

def send_trainer_batch_assignment_notification(trainer_email, trainer_name, batch_name):
    """Alerts course trainer on upcoming batch assignments."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='TRAINER_BATCH_ASSIGNMENT',
        recipient_email=trainer_email,
        subject=TRAINER_BATCH_ASSIGNMENT_SUBJECT,
        template_name='emails/training_course_management/trainer_batch_assignment.html',
        context={
            'trainer_name': trainer_name,
            'batch_name': batch_name,
        }
    )

def send_course_session_reminder_notification(recipient_email, name, session_name, session_time):
    """Dispatches upcoming course session reminders to students/trainers."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='SESSION_REMINDER',
        recipient_email=recipient_email,
        subject=SESSION_REMINDER_SUBJECT,
        template_name='emails/training_course_management/session_reminder.html',
        context={
            'name': name,
            'session_name': session_name,
            'session_time': session_time,
        }
    )

def send_session_update_notification(recipient_email, name, session_name, old_time, new_time):
    """Alerts participants on rescheduling of course sessions."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='SESSION_UPDATE',
        recipient_email=recipient_email,
        subject=SESSION_UPDATE_SUBJECT,
        template_name='emails/training_course_management/session_update.html',
        context={
            'name': name,
            'session_name': session_name,
            'old_time': old_time,
            'new_time': new_time,
        }
    )

def send_meeting_link_notification(recipient_email, name, session_name, meeting_link):
    """Provides video/meeting call link details for online sessions."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='MEETING_LINK',
        recipient_email=recipient_email,
        subject=MEETING_LINK_SUBJECT,
        template_name='emails/training_course_management/meeting_link.html',
        context={
            'name': name,
            'session_name': session_name,
            'meeting_link': meeting_link,
        }
    )

def send_course_material_notification(recipient_email, student_name, course_name, material_name):
    """Alerts course students on document material uploads."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='COURSE_MATERIAL',
        recipient_email=recipient_email,
        subject=COURSE_MATERIAL_SUBJECT,
        template_name='emails/training_course_management/course_material_uploaded.html',
        context={
            'student_name': student_name,
            'course_name': course_name,
            'material_name': material_name,
        }
    )

def send_course_announcement_notification(recipient_email, name, announcement_title, announcement_message):
    """Dispatches administrative announcements to course participants."""
    return send_email_notification(
        module_name='TRAINING_COURSE_MANAGEMENT',
        event_type='COURSE_ANNOUNCEMENT',
        recipient_email=recipient_email,
        subject=COURSE_ANNOUNCEMENT_SUBJECT,
        template_name='emails/training_course_management/course_announcement.html',
        context={
            'name': name,
            'announcement_title': announcement_title,
            'announcement_message': announcement_message,
        }
    )


# ==========================================
# 5. Calendar Event & Conflict Reminders Services
# ==========================================

def check_schedule_conflict(user, start_time, end_time, exclude_event_id=None):
    """Detects if a user has overlapping event slots during the chosen time frame."""
    conflicts = CalendarEvent.objects.filter(
        user=user,
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    if exclude_event_id:
        conflicts = conflicts.exclude(id=exclude_event_id)
    return conflicts.exists()

def create_event(user, title, start_time, end_time, description=None, location=None, meeting_link=None):
    """Validates overlapping conflicts and commits a new event to the DB."""
    if check_schedule_conflict(user, start_time, end_time):
        raise ValueError("Schedule conflict detected for this user in the specified time frame.")
    
    event = CalendarEvent.objects.create(
        user=user,
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        location=location,
        meeting_link=meeting_link
    )
    return event

def update_event(event_id, **kwargs):
    """Updates event parameters after assessing overlap conflicts."""
    event = CalendarEvent.objects.get(id=event_id)
    start_time = kwargs.get('start_time', event.start_time)
    end_time = kwargs.get('end_time', event.end_time)
    
    if check_schedule_conflict(event.user, start_time, end_time, exclude_event_id=event_id):
        raise ValueError("Schedule conflict detected for this user in the specified time frame.")
        
    for key, value in kwargs.items():
        setattr(event, key, value)
        
    event.save()
    return event

def send_session_reminder(trainer_email, session_name, session_time):
    """Shortcut helper dispatching upcoming session alerts."""
    return send_session_reminder_notification(
        trainer=type('MockTrainer', (object,), {'email': trainer_email, 'first_name': trainer_email.split('@')[0], 'username': trainer_email.split('@')[0]})(),
        session_name=session_name,
        session_time=session_time
    )


# ==========================================
# 6. Document Management Services
# ==========================================

def validate_document(file):
    """Runs extension-type and maximum capacity size validations on the raw file."""
    validate_file_type(file)
    validate_file_size(file)
    return True

def upload_document(title, file, related_module, related_id):
    """Validates and creates a Document database entry."""
    validate_document(file)
    extension = file.name.split('.')[-1].lower() if file.name else 'unknown'
    
    document = Document.objects.create(
        title=title,
        file=file,
        file_type=extension,
        related_module=related_module,
        related_id=related_id
    )
    return document


# ==========================================
# 7. Certification & Miscellaneous services
# ==========================================

def generate_certificate(recipient_name, course_name):
    """Generates verification payload simulating PDF certificate compilation."""
    cert_uuid = str(uuid.uuid4())
    return {
        'status': 'success',
        'certificate_id': cert_uuid,
        'recipient_name': recipient_name,
        'course_name': course_name,
        'issued_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }
