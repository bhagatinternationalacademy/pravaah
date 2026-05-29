from django.contrib import admin
from .models import EmailNotificationLog, CalendarEvent, Reminder, Document, Announcement

@admin.register(EmailNotificationLog)
class EmailNotificationLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'module_name', 'event_type', 'subject', 'status', 'created_at')
    list_filter = ('status', 'module_name', 'event_type')
    search_fields = ('recipient_email', 'subject', 'error_message')
    readonly_fields = ('created_at', 'sent_at')

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_time', 'end_time', 'location')
    list_filter = ('start_time', 'user')
    search_fields = ('title', 'description', 'location')

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('event', 'reminder_time', 'sent', 'created_at')
    list_filter = ('sent', 'reminder_time')
    search_fields = ('event__title',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'related_module', 'related_id', 'uploaded_at')
    list_filter = ('file_type', 'related_module', 'uploaded_at')
    search_fields = ('title', 'related_module')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content')
