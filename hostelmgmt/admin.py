from django.contrib import admin
from .models import (
    Hostel, Block, Floor, Room, RoomAllocation,
    RoomTransfer, Visitor, Complaint, MaintenanceRequest, FeePayment
)


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ['hostel_code', 'hostel_name', 'status']
    search_fields = ['hostel_code', 'hostel_name']
    list_filter = ['status']


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['block_id', 'block_name', 'hostel']
    list_filter = ['hostel']


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ['floor_id', 'floor_no', 'block']
    list_filter = ['block']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'floor', 'capacity', 'occupied', 'gender', 'status']
    list_filter = ['status', 'gender', 'floor__floor_no']
    search_fields = ['room_number']
    list_editable = ['status']


@admin.register(RoomAllocation)
class RoomAllocationAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_id', 'room', 'gender',
                    'bed_number', 'allocation_date', 'status']
    list_filter = ['status', 'gender', 'allocation_date']
    search_fields = ['student_id', 'student_name']
    list_editable = ['status']
    date_hierarchy = 'allocation_date'


@admin.register(RoomTransfer)
class RoomTransferAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'from_room', 'to_room', 'request_date', 'status']
    list_filter = ['status', 'request_date']
    search_fields = ['student_id']
    list_editable = ['status']


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['visitor_name', 'student_id', 'relationship', 'mobile', 'checkin', 'checkout']
    search_fields = ['visitor_name', 'student_id', 'mobile']
    list_filter = ['relationship']
    date_hierarchy = 'checkin'


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'room', 'complaint_type', 'complaint_date', 'status']
    list_filter = ['status', 'complaint_type', 'complaint_date']
    search_fields = ['student_id']
    list_editable = ['status']
    date_hierarchy = 'complaint_date'


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['room', 'requested_by', 'request_date', 'status', 'resolved_on']
    list_filter = ['status', 'request_date']
    list_editable = ['status']
    date_hierarchy = 'request_date'


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_no', 'allocation', 'amount', 'payment_mode',
                    'payment_date', 'payment_status']
    list_filter = ['payment_status', 'payment_mode']
    search_fields = ['receipt_no']