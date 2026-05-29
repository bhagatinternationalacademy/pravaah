import json
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models.functions import Cast
from django.db.models import IntegerField, Count, Q
from django.db import transaction
from django.utils import timezone

from .models import (
    Room, RoomAllocation, RoomTransfer, WaitingList,
    Visitor, Complaint, MaintenanceRequest
)
from .forms import VisitorForm, ComplaintForm


# ═════════════════════════════════════════════════════════════
# CONSTANTS
# ═════════════════════════════════════════════════════════════

STUDENT_ROOM_ORDER      = list(range(1, 39))   # 1 → 38 ascending
TRAINER_PREFERRED_ORDER = list(range(1, 39))   # 1 → 38 ascending


# ═════════════════════════════════════════════════════════════
# DATA FETCHING
# ═════════════════════════════════════════════════════════════

def _get_participants():
    try:
        from participantmgmt.models import Participant
        participants = []
        for p in Participant.objects.all():
            participants.append({
                'id':            str(p.pk),
                'name':          getattr(p, 'name', getattr(p, 'full_name', str(p))),
                'gender':        getattr(p, 'gender', 'male'),
                'course':        getattr(p, 'course', ''),
                'checkin_date':  getattr(p, 'checkin_date', None) or getattr(p, 'start_date', None),
                'checkout_date': getattr(p, 'checkout_date', None) or getattr(p, 'end_date', None),
            })
        return participants
    except Exception:
        return [
            {'id': 'STU001', 'name': 'Ravi Kumar',    'gender': 'male',
             'course': 'Python',       'checkin_date': date(2026, 6, 1),  'checkout_date': date(2026, 6, 10)},
            {'id': 'STU002', 'name': 'Anjali Sharma', 'gender': 'female',
             'course': 'Python',       'checkin_date': date(2026, 6, 1),  'checkout_date': date(2026, 6, 10)},
            {'id': 'STU003', 'name': 'Deepak Rao',    'gender': 'male',
             'course': 'Data Science', 'checkin_date': date(2026, 6, 3),  'checkout_date': date(2026, 6, 12)},
            {'id': 'STU004', 'name': 'Priya Nair',    'gender': 'female',
             'course': 'Data Science', 'checkin_date': date(2026, 6, 3),  'checkout_date': date(2026, 6, 12)},
        ]


def _get_trainers():
    try:
        from trainermgmt.models import Trainer
        trainers = []
        for t in Trainer.objects.all():
            trainers.append({
                'id':            str(t.pk),
                'name':          getattr(t, 'name', getattr(t, 'full_name', str(t))),
                'gender':        getattr(t, 'gender', 'male'),
                'department':    getattr(t, 'department', ''),
                'checkin_date':  getattr(t, 'checkin_date', None) or getattr(t, 'start_date', None),
                'checkout_date': getattr(t, 'checkout_date', None) or getattr(t, 'end_date', None),
            })
        return trainers
    except Exception:
        return [
            {'id': 'TRN001', 'name': 'Dr. Suresh Babu',   'gender': 'male',
             'department': 'CS', 'checkin_date': date(2026, 6, 1),  'checkout_date': date(2026, 6, 10)},
            {'id': 'TRN002', 'name': 'Prof. Meena Joshi', 'gender': 'female',
             'department': 'DS', 'checkin_date': date(2026, 6, 3),  'checkout_date': date(2026, 6, 12)},
        ]


# ═════════════════════════════════════════════════════════════
# ALLOCATION STATE QUERIES
# ═════════════════════════════════════════════════════════════

def _already_allocated_ids():
    return set(
        RoomAllocation.objects.filter(status='active')
        .values_list('student_id', flat=True)
    )


def _already_waiting_ids():
    return set(
        WaitingList.objects.filter(status='waiting')
        .values_list('person_id', flat=True)
    )


def _room_date_conflict(room_id, checkin, checkout, allocations_by_room, room_capacity):
    if not checkin or not checkout:
        return False
    block_start   = checkin  - timedelta(days=1)
    block_end     = checkout + timedelta(days=1)
    overlap_count = 0
    for alloc in allocations_by_room.get(room_id, []):
        ci = alloc['checkin_date']
        co = alloc['checkout_date']
        if ci and co and ci <= block_end and co >= block_start:
            overlap_count += 1
    return overlap_count >= room_capacity


# ═════════════════════════════════════════════════════════════
# RECALCULATE ROOM
# ═════════════════════════════════════════════════════════════

def _recalculate_room(room):
    """
    Derive room.occupied / room.gender / room.status from the actual
    active allocations in the DB.

    Called after:
      • auto_allocate  — every room touched during bulk allocation
      • remove_occupant
      • drag_drop_transfer  (both from_room and to_room)
      • security_checkout   ← NEW: when a person physically checks out
    """
    active   = RoomAllocation.objects.filter(room=room, status='active')
    occupied = active.count()

    room.occupied = occupied

    if occupied == 0:
        room.gender = None
        room.status = 'available'
    else:
        room.gender  = active.first().gender
        has_trainer  = active.filter(person_type='trainer').exists()
        if has_trainer:
            room.status = 'full'
        else:
            room.status = 'full' if occupied >= room.capacity else 'available'

    room.save()


# ═════════════════════════════════════════════════════════════
# IN-MEMORY ROOM STATE  (used only inside auto_allocate)
# ═════════════════════════════════════════════════════════════

class _RoomState:
    __slots__ = ('room', 'occupied', 'gender', 'has_trainer', 'capacity', 'db_status')

    def __init__(self, room):
        self.room      = room
        self.capacity  = room.capacity
        self.db_status = room.status
        active         = RoomAllocation.objects.filter(room=room, status='active')
        self.occupied    = active.count()
        self.has_trainer = active.filter(person_type='trainer').exists()
        first            = active.first()
        self.gender      = first.gender if first else None

    @property
    def is_maintenance(self):
        return self.db_status == 'maintenance'

    @property
    def is_full(self):
        return self.has_trainer or self.occupied >= self.capacity

    @property
    def is_partial(self):
        return (not self.has_trainer) and (0 < self.occupied < self.capacity)

    @property
    def is_empty(self):
        return self.occupied == 0

    def add_occupant(self, gender, person_type):
        self.occupied += 1
        self.gender    = gender
        if person_type == 'trainer':
            self.has_trainer = True


def _build_room_states():
    return {int(r.room_number): _RoomState(r) for r in Room.objects.all()}


# ═════════════════════════════════════════════════════════════
# FIND ROOM FOR STUDENT / TRAINER
# ═════════════════════════════════════════════════════════════

def _find_room_for_student(gender, checkin, checkout, states, allocations_by_room):
    # Pass 1: top-up a partially-filled same-gender room.
    for rn in STUDENT_ROOM_ORDER:
        s = states.get(rn)
        if s is None or s.is_maintenance:
            continue
        if (
            s.is_partial
            and s.gender == gender
            and not _room_date_conflict(s.room.pk, checkin, checkout, allocations_by_room, s.capacity)
        ):
            return s

    # Pass 2: open a fresh empty room.
    for rn in STUDENT_ROOM_ORDER:
        s = states.get(rn)
        if s is None or s.is_maintenance:
            continue
        if (
            s.is_empty
            and not _room_date_conflict(s.room.pk, checkin, checkout, allocations_by_room, s.capacity)
        ):
            return s

    return None


def _find_room_for_trainer(gender, checkin, checkout, states, allocations_by_room):
    for rn in TRAINER_PREFERRED_ORDER:
        s = states.get(rn)
        if s is None or s.is_maintenance:
            continue
        if (
            s.is_empty
            and not _room_date_conflict(s.room.pk, checkin, checkout, allocations_by_room, s.capacity)
        ):
            return s
    return None


# ═════════════════════════════════════════════════════════════
# TRANSFER HISTORY HELPER
# ═════════════════════════════════════════════════════════════

def _room_occupant_names(room):
    names = list(
        RoomAllocation.objects.filter(room=room, status='active')
        .values_list('student_name', flat=True)
    )
    return ', '.join(names) if names else ''


# ═════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════

def hostel_dashboard(request):
    return render(request, 'hostelmgmt/dashboard.html', {
        'total_rooms':       Room.objects.count(),
        'available_rooms':   Room.objects.filter(status='available').count(),
        'allocated_rooms':   Room.objects.filter(status='full').count(),
        'total_complaints':  Complaint.objects.filter(status='open').count(),
        'waiting_count':     WaitingList.objects.filter(status='waiting').count(),
        # Security badge: people physically present but not yet checked out
        'pending_checkouts': RoomAllocation.objects.filter(
            status='active', actual_checkout_time__isnull=True
        ).count(),
    })


# ═════════════════════════════════════════════════════════════
# ROOM ALLOCATION VIEW
# ═════════════════════════════════════════════════════════════

def room_allocation(request):
    allocated_ids = _already_allocated_ids()
    waiting_ids   = _already_waiting_ids()

    unallocated_students = [
        s for s in _get_participants()
        if s['id'] not in allocated_ids and s['id'] not in waiting_ids
    ]
    unallocated_trainers = [
        t for t in _get_trainers()
        if t['id'] not in allocated_ids and t['id'] not in waiting_ids
    ]

    active_allocations = (
        RoomAllocation.objects.filter(status='active')
        .select_related('room')
        .order_by('-allocation_id')
    )
    waiting_list = WaitingList.objects.filter(status='waiting').order_by('added_on')

    rooms = (
        Room.objects.all()
        .annotate(room_no_int=Cast('room_number', IntegerField()))
        .order_by('room_no_int')
    )

    rooms_display = []
    for room in rooms:
        has_trainer = RoomAllocation.objects.filter(
            room=room, status='active', person_type='trainer'
        ).exists()
        rooms_display.append({
            'room':               room,
            'effective_capacity': 1 if has_trainer else room.capacity,
            'is_trainer_room':    has_trainer,
        })

    return render(request, 'hostelmgmt/room_allocation.html', {
        'unallocated_students': unallocated_students,
        'unallocated_trainers': unallocated_trainers,
        'active_allocations':   active_allocations,
        'waiting_list':         waiting_list,
        'rooms':                rooms,
        'rooms_display':        rooms_display,
        'total_rooms':          rooms.count(),
        'available_rooms':      rooms.filter(status='available').count(),
        'full_rooms':           rooms.filter(status='full').count(),
        'maintenance_rooms':    rooms.filter(status='maintenance').count(),
    })


# ═════════════════════════════════════════════════════════════
# AUTO ALLOCATE
# ═════════════════════════════════════════════════════════════

@require_POST
@transaction.atomic
def auto_allocate(request):
    allocated_ids = _already_allocated_ids()
    waiting_ids   = _already_waiting_ids()

    students = [
        s for s in _get_participants()
        if s['id'] not in allocated_ids and s['id'] not in waiting_ids
    ]
    trainers = [
        t for t in _get_trainers()
        if t['id'] not in allocated_ids and t['id'] not in waiting_ids
    ]

    states = _build_room_states()

    allocations_by_room: dict[int, list] = {}
    for alloc in RoomAllocation.objects.filter(status='active').values(
        'room_id', 'checkin_date', 'checkout_date'
    ):
        allocations_by_room.setdefault(alloc['room_id'], []).append(alloc)

    student_allocated  = student_waitlisted = 0
    trainer_allocated  = trainer_waitlisted = 0

    female_students = [s for s in students if s['gender'] == 'female']
    male_students   = [s for s in students if s['gender'] == 'male']

    for student in female_students + male_students:
        gender   = student['gender']
        checkin  = student.get('checkin_date')
        checkout = student.get('checkout_date')
        rs = _find_room_for_student(gender, checkin, checkout, states, allocations_by_room)
        if rs:
            RoomAllocation.objects.create(
                room=rs.room, person_type='student',
                student_id=student['id'], student_name=student['name'],
                gender=gender, bed_number=rs.occupied + 1,
                checkin_date=checkin, checkout_date=checkout, status='active',
            )
            rs.add_occupant(gender, 'student')
            allocations_by_room.setdefault(rs.room.pk, []).append(
                {'room_id': rs.room.pk, 'checkin_date': checkin, 'checkout_date': checkout}
            )
            student_allocated += 1
        else:
            WaitingList.objects.create(
                person_type='student', person_id=student['id'],
                person_name=student['name'], gender=gender,
                checkin_date=checkin, checkout_date=checkout, status='waiting',
            )
            student_waitlisted += 1

    for trainer in trainers:
        gender   = trainer['gender']
        checkin  = trainer.get('checkin_date')
        checkout = trainer.get('checkout_date')
        rs = _find_room_for_trainer(gender, checkin, checkout, states, allocations_by_room)
        if rs:
            RoomAllocation.objects.create(
                room=rs.room, person_type='trainer',
                student_id=trainer['id'], student_name=trainer['name'],
                gender=gender, bed_number=1,
                checkin_date=checkin, checkout_date=checkout, status='active',
            )
            rs.add_occupant(gender, 'trainer')
            allocations_by_room.setdefault(rs.room.pk, []).append(
                {'room_id': rs.room.pk, 'checkin_date': checkin, 'checkout_date': checkout}
            )
            trainer_allocated += 1
        else:
            WaitingList.objects.create(
                person_type='trainer', person_id=trainer['id'],
                person_name=trainer['name'], gender=gender,
                checkin_date=checkin, checkout_date=checkout, status='waiting',
            )
            trainer_waitlisted += 1

    modified_pks = {s.room.pk for s in states.values() if s.occupied > 0}
    for room in Room.objects.filter(pk__in=modified_pks):
        _recalculate_room(room)

    if student_allocated == 0 and trainer_allocated == 0 \
            and student_waitlisted == 0 and trainer_waitlisted == 0:
        messages.info(request, "No pending students or trainers to allocate.")
    else:
        messages.success(
            request,
            f"Allocation complete — "
            f"Students: {student_allocated} allocated, {student_waitlisted} waitlisted | "
            f"Trainers: {trainer_allocated} allocated, {trainer_waitlisted} waitlisted"
        )
    return redirect('hostelmgmt:room_allocation')


# ═════════════════════════════════════════════════════════════
# ADMIN CONTROLS
# ═════════════════════════════════════════════════════════════

@require_POST
def remove_occupant(request, allocation_id):
    allocation = get_object_or_404(RoomAllocation, pk=allocation_id)
    room = allocation.room
    allocation.status = 'vacated'
    allocation.save()
    _recalculate_room(room)
    messages.success(request, f"{allocation.student_name} removed successfully.")
    return redirect('hostelmgmt:room_allocation')


@require_POST
def toggle_maintenance(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if room.status == 'maintenance':
        _recalculate_room(room)
        messages.success(request, f"Room {room.room_number} reactivated.")
    else:
        room.status = 'maintenance'
        room.save()
        messages.warning(request, f"Room {room.room_number} set to maintenance.")
    return redirect('hostelmgmt:room_allocation')


# ═════════════════════════════════════════════════════════════
# ROOM TRANSFER PAGE
# ═════════════════════════════════════════════════════════════

def room_transfer(request):
    rooms = (
        Room.objects.all()
        .annotate(room_no_int=Cast('room_number', IntegerField()))
        .order_by('room_no_int')
    )
    rooms_data = []
    for room in rooms:
        occupants = (
            RoomAllocation.objects.filter(room=room, status='active')
            .order_by('bed_number')
            .values('allocation_id', 'student_id', 'student_name',
                    'gender', 'person_type', 'bed_number')
        )
        rooms_data.append({'room': room, 'occupants': list(occupants)})

    transfers = (
        RoomTransfer.objects.all()
        .select_related('from_room', 'to_room')
        .order_by('-transfer_id')[:30]
    )
    return render(request, 'hostelmgmt/room_transfer.html', {
        'rooms_data': rooms_data,
        'transfers':  transfers,
    })


# ═════════════════════════════════════════════════════════════
# DRAG & DROP TRANSFER
# ═════════════════════════════════════════════════════════════

@require_POST
def drag_drop_transfer(request):
    try:
        data          = json.loads(request.body)
        allocation_id = int(data.get('allocation_id'))
        to_room_id    = int(data.get('to_room_id'))
    except (TypeError, ValueError, KeyError):
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    allocation = get_object_or_404(RoomAllocation, pk=allocation_id, status='active')
    to_room    = get_object_or_404(Room, pk=to_room_id)
    from_room  = allocation.room

    if from_room.room_id == to_room.room_id:
        return JsonResponse({'success': False, 'message': 'Source and destination are the same room.'})
    if to_room.status == 'maintenance':
        return JsonResponse({'success': False, 'message': f'Room {to_room.room_number} is under maintenance.'})

    active_in_dest = RoomAllocation.objects.filter(room=to_room, status='active')
    active_count   = active_in_dest.count()

    if active_count >= to_room.capacity:
        return JsonResponse({'success': False, 'message': f'Room {to_room.room_number} is full.'})

    first_dest = active_in_dest.first()
    if first_dest and first_dest.gender != allocation.gender:
        return JsonResponse({
            'success': False,
            'message': f'Gender mismatch — Room {to_room.room_number} is a {first_dest.gender} room.'
        })
    if active_in_dest.filter(person_type='trainer').exists():
        return JsonResponse({'success': False, 'message': 'Trainer room is private — transfer blocked.'})
    if allocation.person_type == 'trainer' and active_count > 0:
        return JsonResponse({'success': False, 'message': 'Trainer requires an empty room.'})

    existing_names = _room_occupant_names(to_room)
    reason = (
        f"{allocation.student_name} moved to Room {to_room.room_number} with {existing_names}"
        if existing_names
        else f"{allocation.student_name} moved to Room {to_room.room_number} (empty room)"
    )

    RoomTransfer.objects.create(
        student_id=allocation.student_id, student_name=allocation.student_name,
        from_room=from_room, to_room=to_room, reason=reason, status='approved',
    )
    allocation.room       = to_room
    allocation.bed_number = active_count + 1
    allocation.save()
    _recalculate_room(from_room)
    _recalculate_room(to_room)

    return JsonResponse({'success': True, 'message': reason})


# ═════════════════════════════════════════════════════════════
# ███████╗███████╗ ██████╗██╗   ██╗██████╗ ██╗████████╗██╗   ██╗
# ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝
# ███████╗█████╗  ██║     ██║   ██║██████╔╝██║   ██║    ╚████╔╝
# ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██║   ██║     ╚██╔╝
# ███████║███████╗╚██████╗╚██████╔╝██║  ██║██║   ██║      ██║
# ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝
#
#  NEW PAGE – Security / Physical Checkout
# ═════════════════════════════════════════════════════════════

def security(request):
    """
    Security desk view.

    Displays ALL currently active allocations split into two panels:

    Panel A — PRESENT  (actual_checkout_time is NULL)
        Everyone physically still inside the building.
        The security officer checks a checkbox + clicks "Checkout" to
        record the exact departure timestamp.

    Panel B — CHECKED OUT TODAY  (actual_checkout_time is set, same date)
        Readonly log of who left today, with the recorded time.

    Filters (GET params):
        q         — name or room search
        gender    — 'male' | 'female' | ''
        type      — 'student' | 'trainer' | ''
        overdue   — '1'  show only people whose planned checkout_date < today
    """
    today    = date.today()
    search   = request.GET.get('q', '').strip()
    gender   = request.GET.get('gender', '')
    ptype    = request.GET.get('type', '')
    overdue  = request.GET.get('overdue', '')

    # ── Base queryset: all active allocations ─────────────────────────────
    base_qs = (
        RoomAllocation.objects.filter(status='active')
        .select_related('room')
        .order_by('room__room_number', 'student_name')
    )

    if search:
        base_qs = base_qs.filter(
            Q(student_name__icontains=search) |
            Q(room__room_number__icontains=search) |
            Q(student_id__icontains=search)
        )
    if gender:
        base_qs = base_qs.filter(gender=gender)
    if ptype:
        base_qs = base_qs.filter(person_type=ptype)

    # Panel A: physically present (not yet checked out by security)
    present_qs = base_qs.filter(actual_checkout_time__isnull=True)
    if overdue == '1':
        present_qs = present_qs.filter(checkout_date__lt=today)

    # Panel B: checked out today
    checked_out_today_qs = (
        RoomAllocation.objects.filter(
            status='vacated',
            actual_checkout_time__date=today,
        )
        .select_related('room')
        .order_by('-actual_checkout_time')
    )

    # Summary counts for stat cards
    total_present   = RoomAllocation.objects.filter(
        status='active', actual_checkout_time__isnull=True
    ).count()
    total_overdue   = RoomAllocation.objects.filter(
        status='active', actual_checkout_time__isnull=True,
        checkout_date__lt=today
    ).count()
    checked_out_cnt = checked_out_today_qs.count()

    return render(request, 'hostelmgmt/security.html', {
        'present_list':        present_qs,
        'checked_out_today':   checked_out_today_qs,
        'total_present':       total_present,
        'total_overdue':       total_overdue,
        'checked_out_today_count': checked_out_cnt,
        'today':               today,
        # Pass filter values back so the form stays populated
        'filter_q':       search,
        'filter_gender':  gender,
        'filter_type':    ptype,
        'filter_overdue': overdue,
    })


@require_POST
def security_checkout(request, allocation_id):
    """
    Called when the security officer ticks the checkbox and submits.

    Steps:
      1. Stamp actual_checkout_time = now().
      2. Record who processed it (request.user).
      3. Mark the allocation as 'vacated'.
      4. _recalculate_room() → room becomes 'available' or partial.

    Returns JSON so the page can update without a full reload.
    """
    allocation = get_object_or_404(RoomAllocation, pk=allocation_id, status='active')
    room       = allocation.room

    now = timezone.now()

    allocation.actual_checkout_time = now
    allocation.checked_out_by       = request.user if request.user.is_authenticated else None
    allocation.status               = 'vacated'
    allocation.save()

    # Update room occupancy / status immediately.
    _recalculate_room(room)

    return JsonResponse({
        'success':       True,
        'name':          allocation.student_name,
        'room':          room.room_number,
        'checkout_time': now.strftime('%d %b %Y, %I:%M %p'),
        'room_status':   room.status,      # 'available' or 'full'
        'room_occupied': room.occupied,
        'room_capacity': room.capacity,
        'message':       (
            f"{allocation.student_name} checked out from Room {room.room_number} "
            f"at {now.strftime('%I:%M %p')}."
        ),
    })


@require_POST
def security_checkout_bulk(request):
    """
    Checkout multiple people at once.
    POST body (JSON): { "allocation_ids": [1, 2, 3] }
    """
    try:
        data           = json.loads(request.body)
        allocation_ids = [int(x) for x in data.get('allocation_ids', [])]
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    if not allocation_ids:
        return JsonResponse({'success': False, 'message': 'No IDs provided.'})

    allocations = RoomAllocation.objects.filter(
        pk__in=allocation_ids, status='active'
    ).select_related('room')

    now           = timezone.now()
    processed     = []
    rooms_to_fix  = set()

    for alloc in allocations:
        alloc.actual_checkout_time = now
        alloc.checked_out_by       = request.user if request.user.is_authenticated else None
        alloc.status               = 'vacated'
        alloc.save()
        rooms_to_fix.add(alloc.room)
        processed.append(alloc.student_name)

    for room in rooms_to_fix:
        _recalculate_room(room)

    return JsonResponse({
        'success':   True,
        'count':     len(processed),
        'names':     processed,
        'message':   f"{len(processed)} occupant(s) checked out successfully.",
    })


# ═════════════════════════════════════════════════════════════
# VISITORS
# ═════════════════════════════════════════════════════════════

# def visitors(request):
#     visitor_list = Visitor.objects.all().order_by('-visitor_id')[:30]
#     return render(request, 'hostelmgmt/visitors.html', {'visitor_list': visitor_list})


# def book_gate_pass(request):
#     if request.method == 'POST':
#         form = VisitorForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Gate pass booked successfully.')
#             return redirect('hostelmgmt:visitors')
#     else:
#         form = VisitorForm()
#     return render(request, 'hostelmgmt/book_gate_pass.html', {'form': form})

# ═════════════════════════════════════════════════════════════
# VISITORS
# ═════════════════════════════════════════════════════════════


def visitors(request):
    visitor_list = Visitor.objects.all().order_by('-visitor_id')[:50]
    return render(request, 'hostelmgmt/visitors.html', {
        'visitor_list': visitor_list,
    })


def book_gate_pass(request):
    """
    Admin fills visitor form → save → generate PDF → email to visitor.
    PDF is sent to visitor's email only — no download on admin PC.
    """
    if request.method == 'POST':
        form = VisitorForm(request.POST)

        if form.is_valid():
            visitor = form.save()

            # ── Step 1: Generate PDF in memory ───────────────────────────
            pdf_bytes = None
            try:
                from .utils.gate_pass_pdf import generate_gate_pass_pdf
                pdf_bytes = generate_gate_pass_pdf(visitor)
            except Exception as exc:
                messages.warning(
                    request,
                    f'⚠️  Gate pass saved but PDF generation failed: {exc}'
                )

            # ── Step 2: Email PDF to visitor (no browser download) ────────
            if pdf_bytes:
                email_address = (visitor.visitor_email or '').strip()
                if email_address:
                    try:
                        from django.core.mail import EmailMessage
                        from django.conf import settings as django_settings

                        gate_pass_id = visitor.gate_pass_id()
                        filename     = f'GatePass_{gate_pass_id}.pdf'

                        email = EmailMessage(
                            subject=f'Your Hostel Visitor Gate Pass — {gate_pass_id}',
                            body=(
                                f'Dear {visitor.visitor_name},\n\n'
                                f'Your gate pass has been approved.\n'
                                f'Gate Pass ID : {gate_pass_id}\n\n'
                                f'Please find your gate pass attached.\n\n'
                                f'Important:\n'
                                f'  • Carry a valid photo ID (Aadhaar / PAN / Passport).\n'
                                f'  • This pass is valid only for the specified date and time.\n'
                                f'  • Report at the security desk on arrival.\n'
                                f'  • Visiting hours: 9:00 AM - 8:00 PM only.\n\n'
                                f'Regards,\n'
                                f'Hostel Administration\n'
                                f'PRAVAAH Integrated Management Suite'
                            ),
                            from_email=getattr(
                                django_settings, 'DEFAULT_FROM_EMAIL', 'admin@pravaah.com'
                            ),
                            to=[email_address],
                        )
                        email.attach(filename, pdf_bytes, 'application/pdf')
                        email.send(fail_silently=False)

                        messages.success(
                            request,
                            f'✅ Gate pass created and emailed to {email_address}.'
                        )
                    except Exception as exc:
                        messages.warning(
                            request,
                            f'✅ Gate pass saved but email could not be sent: {exc}'
                        )
                else:
                    messages.warning(
                        request,
                        '✅ Gate pass saved. No email sent — visitor email not provided.'
                    )

            return redirect('hostelmgmt:visitors')

        else:
            messages.error(request, '❌ Please fix the errors below.')

    else:
        form = VisitorForm()

    return render(request, 'hostelmgmt/book_gate_pass.html', {'form': form})


# ─────────────────────────────────────────────────────────────
#  COMPLAINTS  (main page)
# ─────────────────────────────────────────────────────────────
def complaints(request):
    """
    GET  → render the complaints page
    POST → submit a new complaint
    """
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        room    = Room.objects.filter(pk=room_id).first() if room_id else None
 
        Complaint.objects.create(
            student_id     = request.POST.get('student_id', '').strip() or None,
            student_name   = request.POST.get('student_name', '').strip() or 'Unknown',
            room           = room,
            complaint_type = request.POST['complaint_type'],
            description    = request.POST['description'],
            priority       = request.POST.get('priority', 'medium'),
        )
        messages.success(request, 'Complaint submitted successfully.')
        return redirect('hostelmgmt:complaints')
 
    complaint_list = Complaint.objects.select_related('room').all()
 
    ctx = {
        'complaint_list':   complaint_list,
        'rooms':            Room.objects.all(),
        # ── counts for stat cards ──
        'open_count':       complaint_list.filter(status='open').count(),
        'inprogress_count': complaint_list.filter(status='in_progress').count(),
        'resolved_count':   complaint_list.filter(status='resolved').count(),
        'closed_count':     complaint_list.filter(status='closed').count(),
        'total_count':      complaint_list.count(),
    }
    return render(request, 'hostelmgmt/complaints.html', ctx)
 
 
# ─────────────────────────────────────────────────────────────
#  COMPLAINT DETAIL  (AJAX – returns JSON for the modal)
# ─────────────────────────────────────────────────────────────
@require_GET
def complaint_detail(request, complaint_id):
    """
    Called by the JS on the complaints page when the admin clicks a card.
    Returns full complaint data as JSON so the modal can be populated.
    """
    c = get_object_or_404(Complaint, pk=complaint_id)
    return JsonResponse({
        'id':             c.pk,
        'ref':            f'CMP-{c.pk:04d}',
        'student_name':   c.student_name,
        'student_id':     c.student_id or '—',
        'room':           str(c.room) if c.room else '—',
        'complaint_type': c.get_complaint_type_display(),
        'description':    c.description,
        'priority':       c.priority,
        'priority_label': c.get_priority_display(),
        'status':         c.status,
        'status_label':   c.get_status_display(),
        'admin_notes':    c.admin_notes or '',
        'assigned_to':    c.assigned_to or '',
        'created_at':     c.created_at.strftime('%d %b %Y, %I:%M %p'),
        'updated_at':     c.updated_at.strftime('%d %b %Y, %I:%M %p'),
        'resolved_at':    c.resolved_at.strftime('%d %b %Y, %I:%M %p') if c.resolved_at else None,
        'days_open':      c.days_open,
    })
 
 
# ─────────────────────────────────────────────────────────────
#  UPDATE COMPLAINT STATUS  (AJAX POST)
# ─────────────────────────────────────────────────────────────
@require_POST
def update_complaint_status(request, complaint_id):
    """
    AJAX endpoint called when admin submits the status-change form inside
    the detail modal.  Returns updated counts so the stat cards refresh
    without a full page reload.
    """
    c = get_object_or_404(Complaint, pk=complaint_id)
 
    new_status  = request.POST.get('status',      c.status)
    admin_notes = request.POST.get('admin_notes', c.admin_notes or '')
    assigned_to = request.POST.get('assigned_to', c.assigned_to or '')
 
    c.status      = new_status
    c.admin_notes = admin_notes
    c.assigned_to = assigned_to
    c.save()   # resolved_at is auto-stamped inside model.save()
 
    # Return fresh counts so the UI updates the stat cards without reload
    all_c = Complaint.objects.all()
    return JsonResponse({
        'ok':             True,
        'new_status':     c.status,
        'status_label':   c.get_status_display(),
        'resolved_at':    c.resolved_at.strftime('%d %b %Y, %I:%M %p') if c.resolved_at else None,
        'updated_at':     c.updated_at.strftime('%d %b %Y, %I:%M %p'),
        'open_count':       all_c.filter(status='open').count(),
        'inprogress_count': all_c.filter(status='in_progress').count(),
        'resolved_count':   all_c.filter(status='resolved').count(),
        'closed_count':     all_c.filter(status='closed').count(),
        'total_count':      all_c.count(),
    })
 
 
# ─────────────────────────────────────────────────────────────
#  REPORTS  (updated to include complaint breakdown)
# ─────────────────────────────────────────────────────────────
def reports(request):
    from .models import RoomAllocation, WaitingList, Visitor, MaintenanceRequest
    from django.db.models.functions import Cast
    from django.db.models import IntegerField, Count
 
    allocations  = (
        RoomAllocation.objects.filter(status='active')
        .select_related('room')
        .order_by('room__room_number')
    )
    waiting_list = WaitingList.objects.all().order_by('added_on')
    room_wise    = (
        Room.objects.all()
        .annotate(room_no_int=Cast('room_number', IntegerField()))
        .order_by('room_no_int')
    )
    all_complaints = Complaint.objects.select_related('room').all()
 
    # Complaint breakdown by type
    type_breakdown = (
        all_complaints.values('complaint_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    # Label the types
    type_labels = dict(Complaint.TYPE_CHOICES)
    for row in type_breakdown:
        row['label'] = type_labels.get(row['complaint_type'], row['complaint_type'])
 
    ctx = {
        # Room stats
        'total_allocated':   allocations.count(),
        'total_visitors':    Visitor.objects.count(),
        'available_rooms':   Room.objects.filter(status='available').count(),
        'full_rooms':        Room.objects.filter(status='full').count(),
        'waiting_count':     waiting_list.count(),
        'room_wise':         room_wise,
        'allocations':       allocations,
        'waiting_list':      waiting_list,
 
        # Complaint stats (live)
        'total_complaints':      all_complaints.count(),
        'open_complaints':       all_complaints.filter(status='open').count(),
        'inprogress_complaints': all_complaints.filter(status='in_progress').count(),
        'resolved_complaints':   all_complaints.filter(status='resolved').count(),
        'closed_complaints':     all_complaints.filter(status='closed').count(),
        'complaint_list':        all_complaints[:50],
        'type_breakdown':        list(type_breakdown),
 
        # Maintenance stats
        'mnt_pending':    MaintenanceRequest.objects.filter(status='pending').count(),
        'mnt_inprogress': MaintenanceRequest.objects.filter(status='in_progress').count(),
        'mnt_resolved':   MaintenanceRequest.objects.filter(status='resolved').count(),
    }
    return render(request, 'hostelmgmt/reports.html', ctx)