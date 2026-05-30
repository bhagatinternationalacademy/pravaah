"""
Django Admin configuration for the Billing Management module.

Registers ``Bill``, ``BillHistory``, and ``Notification`` models with
customised list displays, filters, and search fields for efficient
back-office management.
"""

from django.contrib import admin

from .models import Bill, BillHistory, Notification


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Admin interface for managing bills."""

    list_display = [
        'bill_number',
        'bill_title',
        'trainer',
        'bill_amount',
        'current_status',
        'uploaded_at',
    ]
    list_filter = ['current_status', 'uploaded_at']
    search_fields = [
        'bill_number',
        'bill_title',
        'trainer__username',
        'trainer__first_name',
    ]
    readonly_fields = ['uploaded_at', 'final_approved_at']


@admin.register(BillHistory)
class BillHistoryAdmin(admin.ModelAdmin):
    """Admin interface for viewing bill audit-trail entries."""

    list_display = ['bill', 'action_taken', 'action_by', 'timestamp']
    list_filter = ['action_taken', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for managing in-app notifications."""

    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    readonly_fields = ['created_at']
