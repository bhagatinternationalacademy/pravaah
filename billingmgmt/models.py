"""
Models for the Billing Management module.

Defines the core data structures for bill lifecycle management:
- Bill: Represents a billing document submitted by a trainer.
- BillHistory: Audit trail tracking every status change on a bill.
- Notification: In-app notifications sent to users during bill processing.
"""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Bill(models.Model):
    """
    Represents a bill submitted by a trainer for review and payment processing.

    The bill progresses through a multi-stage approval workflow:
    SUBMITTED → UNDER_ACCOUNTS_REVIEW → APPROVED_BY_ACCOUNTS →
    UNDER_TRAINER_ADMIN_REVIEW → PAYMENT_CLEARED

    At any review stage the bill may be rejected, halting the workflow.
    """

    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_ACCOUNTS_REVIEW', 'Under Accounts Review'),
        ('APPROVED_BY_ACCOUNTS', 'Approved by Accounts'),
        ('REJECTED_BY_ACCOUNTS', 'Rejected by Accounts'),
        ('UNDER_TRAINER_ADMIN_REVIEW', 'Under Trainer Admin Review'),
        ('PAYMENT_CLEARED', 'Payment Cleared'),
        ('REJECTED_BY_TRAINER_ADMIN', 'Rejected by Trainer Admin'),
    ]

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bills',
        help_text='The trainer who submitted this bill.',
    )
    bill_title = models.CharField(
        max_length=255,
        help_text='A descriptive title for the bill.',
    )
    bill_number = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique bill/invoice number.',
    )
    bill_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Total amount of the bill in INR.',
    )
    training_program = models.CharField(
        max_length=255,
        help_text='Name of the training program this bill is associated with.',
    )
    bill_pdf = models.FileField(
        upload_to='bills/pdfs/',
        help_text='Uploaded PDF copy of the bill.',
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the bill was first uploaded.',
    )
    current_status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='SUBMITTED',
        help_text='Current workflow status of the bill.',
    )
    final_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the bill received final approval and payment was cleared.',
    )
    remarks = models.TextField(
        blank=True,
        default='',
        help_text='Latest remarks or reason for rejection.',
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'

    def __str__(self):
        return f'{self.bill_number} - {self.bill_title}'

    def clean(self):
        """Validate that the uploaded file has a .pdf extension."""
        super().clean()
        if self.bill_pdf:
            ext = os.path.splitext(self.bill_pdf.name)[1].lower()
            if ext != '.pdf':
                raise ValidationError(
                    {'bill_pdf': 'Only PDF files are allowed.'}
                )


class BillHistory(models.Model):
    """
    Immutable audit-trail entry recording a single action taken on a bill.

    Every status transition, approval, or rejection creates a new
    BillHistory record so the complete lifecycle is traceable.
    """

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='history',
        help_text='The bill this history entry belongs to.',
    )
    action_taken = models.CharField(
        max_length=100,
        help_text='Short description of the action (e.g. "Approved by Accounts").',
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text='The user who performed this action.',
    )
    remarks = models.TextField(
        blank=True,
        default='',
        help_text='Optional remarks associated with this action.',
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When this action was recorded.',
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Bill History'
        verbose_name_plural = 'Bill Histories'

    def __str__(self):
        return f'{self.bill.bill_number} - {self.action_taken}'


class Notification(models.Model):
    """
    In-app notification delivered to a user during the billing workflow.

    Notifications are created automatically when bills change status and
    can be marked as read by the recipient.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='billing_notifications',
        help_text='The user who receives this notification.',
    )
    title = models.CharField(
        max_length=255,
        help_text='Short notification headline.',
    )
    message = models.TextField(
        help_text='Full notification body.',
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the user has read this notification.',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this notification was created.',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'{self.title} - {self.user.username}'
