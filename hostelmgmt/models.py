from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Hostel(models.Model):
    hostel_id   = models.AutoField(primary_key=True)
    hostel_code = models.CharField(max_length=20, unique=True)
    hostel_name = models.CharField(max_length=100)
    address     = models.TextField()
    status      = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active'
    )

    def __str__(self):
        return self.hostel_name

    class Meta:
        db_table = 'hostels'


class Block(models.Model):
    block_id   = models.AutoField(primary_key=True)
    hostel     = models.ForeignKey(Hostel, on_delete=models.CASCADE)
    block_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.hostel.hostel_name} – {self.block_name}"

    class Meta:
        db_table = 'blocks'


class Floor(models.Model):
    floor_id = models.AutoField(primary_key=True)
    block    = models.ForeignKey(Block, on_delete=models.CASCADE)
    floor_no = models.IntegerField()

    def __str__(self):
        return f"Floor {self.floor_no} – {self.block.block_name}"

    class Meta:
        db_table = 'floors'


class Room(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female')]
    STATUS_CHOICES = [
        ('available',   'Available'),
        ('full',        'Full'),
        ('maintenance', 'Under Maintenance'),
    ]

    room_id     = models.AutoField(primary_key=True)
    floor       = models.ForeignKey(Floor, on_delete=models.CASCADE)
    room_number = models.CharField(max_length=10)
    capacity    = models.IntegerField(default=2)
    occupied    = models.IntegerField(default=0)
    gender      = models.CharField(
        max_length=10, choices=GENDER_CHOICES, null=True, blank=True
    )
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='available'
    )

    def is_available(self):
        return self.status != 'maintenance' and self.occupied < self.capacity

    def vacancy(self):
        return self.capacity - self.occupied

    def __str__(self):
        return f"Room {self.room_number}"

    class Meta:
        db_table = 'rooms'


class RoomAllocation(models.Model):
    """Stores student-to-room allocations (auto-allocated from participantmgmt)."""

    GENDER_CHOICES      = [('male', 'Male'), ('female', 'Female')]
    STATUS_CHOICES      = [('active', 'Active'), ('vacated', 'Vacated')]
    PERSON_TYPE_CHOICES = [('student', 'Student'), ('trainer', 'Trainer')]

    allocation_id  = models.AutoField(primary_key=True)
    room           = models.ForeignKey(Room, on_delete=models.CASCADE)

    person_type    = models.CharField(
        max_length=10, choices=PERSON_TYPE_CHOICES, default='student'
    )
    student_id     = models.CharField(max_length=50)
    student_name   = models.CharField(max_length=100)
    gender         = models.CharField(max_length=10, choices=GENDER_CHOICES)
    bed_number     = models.IntegerField()

    checkin_date   = models.DateField(null=True, blank=True)
    checkout_date  = models.DateField(null=True, blank=True)   # planned checkout date from source

    # ── NEW: Security checkout fields ────────────────────────────────────
    # actual_checkout_time: set by the security desk when the person
    #   physically leaves the building.  Null means not yet checked out.
    actual_checkout_time = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp recorded by security when occupant physically checks out."
    )

    # checked_out_by: optional — which admin/security user ticked checkout.
    checked_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='security_checkouts',
        help_text="Staff member who processed the checkout."
    )
    # ─────────────────────────────────────────────────────────────────────

    allocation_date = models.DateField(auto_now_add=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    @property
    def is_checked_out(self):
        """True when security has physically processed the checkout."""
        return self.actual_checkout_time is not None

    def __str__(self):
        return f"{self.student_name} → Room {self.room.room_number}"

    class Meta:
        db_table = 'room_allocations'


class WaitingList(models.Model):
    """Students/trainers who could not be allocated due to no available rooms."""

    GENDER_CHOICES      = [('male', 'Male'), ('female', 'Female')]
    PERSON_TYPE_CHOICES = [('student', 'Student'), ('trainer', 'Trainer')]
    STATUS_CHOICES      = [
        ('waiting',   'Waiting'),
        ('allocated', 'Allocated'),
        ('cancelled', 'Cancelled'),
    ]

    waiting_id    = models.AutoField(primary_key=True)
    person_type   = models.CharField(max_length=10, choices=PERSON_TYPE_CHOICES, default='student')
    person_id     = models.CharField(max_length=50)
    person_name   = models.CharField(max_length=100)
    gender        = models.CharField(max_length=10, choices=GENDER_CHOICES)
    checkin_date  = models.DateField(null=True, blank=True)
    checkout_date = models.DateField(null=True, blank=True)
    added_on      = models.DateField(auto_now_add=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')

    def __str__(self):
        return f"[WAITING] {self.person_name}"

    class Meta:
        db_table = 'waiting_list'


class RoomTransfer(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    transfer_id  = models.AutoField(primary_key=True)
    student_id   = models.CharField(max_length=50)
    student_name = models.CharField(max_length=100, blank=True)
    from_room    = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='transfers_from'
    )
    to_room      = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='transfers_to'
    )
    reason       = models.TextField(blank=True, default='Drag & Drop Transfer')
    request_date = models.DateField(auto_now_add=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')

    def __str__(self):
        return f"{self.student_name}: Room {self.from_room} → {self.to_room}"

    class Meta:
        db_table = 'room_transfers'


class Visitor(models.Model):
    visitor_id   = models.AutoField(primary_key=True)
    student_id   = models.CharField(max_length=20)
    visitor_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    mobile       = models.CharField(max_length=15)
    checkin      = models.DateTimeField()
    checkout     = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.visitor_name} visiting {self.student_id}"

    class Meta:
        db_table = 'visitors'


class Complaint(models.Model):
    COMPLAINT_TYPES = [
        ('electrical', 'Electrical'),
        ('plumbing',   'Plumbing'),
        ('furniture',  'Furniture'),
        ('cleanliness','Cleanliness'),
        ('other',      'Other'),
    ]
    STATUS_CHOICES = [
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
    ]

    complaint_id   = models.AutoField(primary_key=True)
    student_id     = models.CharField(max_length=20)
    room           = models.ForeignKey(Room, on_delete=models.CASCADE)
    complaint_type = models.CharField(max_length=30, choices=COMPLAINT_TYPES)
    description    = models.TextField()
    complaint_date = models.DateField(auto_now_add=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return f"{self.get_complaint_type_display()} – {self.student_id}"

    class Meta:
        db_table = 'complaints'


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
    ]

    request_id   = models.AutoField(primary_key=True)
    room         = models.ForeignKey(Room, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    request_date = models.DateField(auto_now_add=True)
    description  = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolved_on  = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Maintenance – Room {self.room.room_number}"

    class Meta:
        db_table = 'maintenance_requests'


class FeePayment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('cash',   'Cash'),
        ('online', 'Online'),
        ('dd',     'Demand Draft'),
    ]
    STATUS_CHOICES = [
        ('paid',    'Paid'),
        ('pending', 'Pending'),
        ('failed',  'Failed'),
    ]

    payment_id     = models.AutoField(primary_key=True)
    allocation     = models.ForeignKey(RoomAllocation, on_delete=models.CASCADE)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date   = models.DateField()
    payment_mode   = models.CharField(max_length=30, choices=PAYMENT_MODE_CHOICES)
    receipt_no     = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment {self.receipt_no}"

    class Meta:
        db_table = 'fee_payments'