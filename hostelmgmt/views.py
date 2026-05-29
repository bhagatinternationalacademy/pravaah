import json
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models.functions import Cast
<<<<<<< HEAD
from django.db.models import IntegerField, Count, Q
from django.db import transaction
from django.utils import timezone
=======
from django.db.models import IntegerField
from django.db import transaction
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa

from .models import (
    Room, RoomAllocation, RoomTransfer, WaitingList,
    Visitor, Complaint, MaintenanceRequest
)
from .forms import VisitorForm, ComplaintForm


# ═════════════════════════════════════════════════════════════
# CONSTANTS
# ═════════════════════════════════════════════════════════════
<<<<<<< HEAD

STUDENT_ROOM_ORDER      = list(range(1, 39))   # 1 → 38 ascending
TRAINER_PREFERRED_ORDER = list(range(1, 39))   # 1 → 38 ascending
=======
#
# STUDENT_ROOM_ORDER:
#   Generic ascending 1→38 for BOTH genders.
#   No fixed female-priority ranges.  Allocation is purely driven by
#   gender, occupancy, availability, and maintenance status.
#   Females fill room 1 first; if room 1 is taken by females, males
#   skip it (gender check) and fill room 2, etc.
#
# TRAINER_PREFERRED_ORDER:
#   Also ascending 1→38.  After all students are placed, trainers
#   claim the lowest-numbered empty rooms (1, 2, 3 …).

STUDENT_ROOM_ORDER  = list(range(1, 39))   # rooms 1 – 38, ascending
TRAINER_PREFERRED_ORDER = list(range(1, 39))  # rooms 1 – 38, ascending
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa


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
<<<<<<< HEAD
    if not checkin or not checkout:
        return False
    block_start   = checkin  - timedelta(days=1)
    block_end     = checkout + timedelta(days=1)
=======
    """
    FIX: The old version returned True on the FIRST overlap found,
    blocking the room even when a second bed was still free.

    Correct behaviour:
        Count how many existing active allocations on this room have
        date ranges that overlap with [checkin-1 … checkout+1].
        The room is only truly 'date-conflicted' when that count
        reaches or exceeds room_capacity — i.e. every bed is spoken for
        during the requested window.

    This allows two students with different course dates to share a
    capacity-2 room as long as at most one of them occupies it on any
    given day.
    """
    if not checkin or not checkout:
        return False

    block_start = checkin  - timedelta(days=1)
    block_end   = checkout + timedelta(days=1)

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    overlap_count = 0
    for alloc in allocations_by_room.get(room_id, []):
        ci = alloc['checkin_date']
        co = alloc['checkout_date']
        if ci and co and ci <= block_end and co >= block_start:
            overlap_count += 1
<<<<<<< HEAD
=======

    # Room is fully blocked only when every bed is date-conflicted.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    return overlap_count >= room_capacity


# ═════════════════════════════════════════════════════════════
<<<<<<< HEAD
# RECALCULATE ROOM
=======
# RECALCULATE ROOM  (always driven by real DB allocations)
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
# ═════════════════════════════════════════════════════════════

def _recalculate_room(room):
    """
    Derive room.occupied / room.gender / room.status from the actual
<<<<<<< HEAD
    active allocations in the DB.

    Called after:
      • auto_allocate  — every room touched during bulk allocation
      • remove_occupant
      • drag_drop_transfer  (both from_room and to_room)
      • security_checkout   ← NEW: when a person physically checks out
=======
    active allocations stored in the DB.  Called after every create /
    vacate / transfer so the Room row is always consistent.

    Trainer rule:
        A trainer in the room → status = 'full' immediately regardless
        of how many physical beds the room has.  The display will read
        "1/1" because the template uses effective_capacity (see
        room_allocation view and room_allocation.html).
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    """
    active   = RoomAllocation.objects.filter(room=room, status='active')
    occupied = active.count()

    room.occupied = occupied

    if occupied == 0:
        room.gender = None
        room.status = 'available'
    else:
<<<<<<< HEAD
        room.gender  = active.first().gender
        has_trainer  = active.filter(person_type='trainer').exists()
        if has_trainer:
=======
        room.gender     = active.first().gender
        has_trainer     = active.filter(person_type='trainer').exists()
        if has_trainer:
            # Trainer present → room is private and fully occupied.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
            room.status = 'full'
        else:
            room.status = 'full' if occupied >= room.capacity else 'available'

    room.save()


# ═════════════════════════════════════════════════════════════
# IN-MEMORY ROOM STATE  (used only inside auto_allocate)
# ═════════════════════════════════════════════════════════════

class _RoomState:
<<<<<<< HEAD
=======
    """
    Lightweight in-memory mirror of a Room row.
    Built once at the start of auto_allocate and mutated as allocations
    are created, so _find_room_* always sees the latest state without
    issuing repeated SELECT queries inside the allocation loop.
    """
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
=======
        # Trainer room is always considered full (private).
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
        return self.has_trainer or self.occupied >= self.capacity

    @property
    def is_partial(self):
<<<<<<< HEAD
=======
        """Has at least one student but still has a free bed."""
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
=======
    """Return { room_number_int: _RoomState } for every room."""
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    return {int(r.room_number): _RoomState(r) for r in Room.objects.all()}


# ═════════════════════════════════════════════════════════════
<<<<<<< HEAD
# FIND ROOM FOR STUDENT / TRAINER
# ═════════════════════════════════════════════════════════════

def _find_room_for_student(gender, checkin, checkout, states, allocations_by_room):
    # Pass 1: top-up a partially-filled same-gender room.
=======
# FIND ROOM FOR STUDENT
# ═════════════════════════════════════════════════════════════

def _find_room_for_student(gender, checkin, checkout, states, allocations_by_room):
    """
    FIX: Generic ascending order 1→38 for BOTH genders.

    Old code used FEMALE_PRIORITY_ROOMS / MALE_PREFERRED_ROOMS with gaps
    (e.g. females skipped rooms 1-3, males skipped rooms 1-6 and 14-16).
    Those gaps caused scattered allocation and lost usable rooms.

    New behaviour:
        Pass 1 — top up a partially-filled same-gender room (fill-first).
        Pass 2 — open the lowest-numbered empty room available.
    Both passes walk rooms 1, 2, 3 … 38 in order.

    Gender segregation is enforced naturally:
        If room 1 is occupied by females, a male student reaches Pass 1,
        sees room 1 has gender='female', skips it, and opens room 2.
    """
    # Pass 1: Fill an existing partial same-gender room.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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

<<<<<<< HEAD
    # Pass 2: open a fresh empty room.
=======
    # Pass 2: Open a brand-new empty room.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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


<<<<<<< HEAD
def _find_room_for_trainer(gender, checkin, checkout, states, allocations_by_room):
=======
# ═════════════════════════════════════════════════════════════
# FIND ROOM FOR TRAINER
# ═════════════════════════════════════════════════════════════

def _find_room_for_trainer(gender, checkin, checkout, states, allocations_by_room):
    """
    Trainers always need a completely empty room (private).

    FIX: TRAINER_PREFERRED_ORDER is now ascending (1, 2, 3 …).
    Old code used descending order (38, 37 …) which caused trainers to
    always land in the last rooms instead of the first available ones.

    Because students are allocated before trainers, the lowest-numbered
    rooms will already be occupied by students.  Trainers naturally get
    the next available empty room from the bottom up — e.g. if students
    fill rooms 1–4, trainers get room 5, 6, etc.
    """
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    for rn in TRAINER_PREFERRED_ORDER:
        s = states.get(rn)
        if s is None or s.is_maintenance:
            continue
        if (
            s.is_empty
            and not _room_date_conflict(s.room.pk, checkin, checkout, allocations_by_room, s.capacity)
        ):
            return s
<<<<<<< HEAD
=======

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    return None


# ═════════════════════════════════════════════════════════════
# TRANSFER HISTORY HELPER
# ═════════════════════════════════════════════════════════════

def _room_occupant_names(room):
<<<<<<< HEAD
=======
    """
    Return comma-separated names of every active occupant in *room*.
    Used by drag_drop_transfer to write rich history such as:
        "Anjali Sharma moved to Room 5 with Priya Nair"
    """
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
        'total_rooms':       Room.objects.count(),
        'available_rooms':   Room.objects.filter(status='available').count(),
        'allocated_rooms':   Room.objects.filter(status='full').count(),
        'total_complaints':  Complaint.objects.filter(status='open').count(),
        'waiting_count':     WaitingList.objects.filter(status='waiting').count(),
        # Security badge: people physically present but not yet checked out
        'pending_checkouts': RoomAllocation.objects.filter(
            status='active', actual_checkout_time__isnull=True
        ).count(),
=======
        'total_rooms':      Room.objects.count(),
        'available_rooms':  Room.objects.filter(status='available').count(),
        'allocated_rooms':  Room.objects.filter(status='full').count(),
        'total_complaints': Complaint.objects.filter(status='open').count(),
        'waiting_count':    WaitingList.objects.filter(status='waiting').count(),
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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

<<<<<<< HEAD
=======
    # ── Build per-room display metadata ────────────────────────────────────
    # effective_capacity: trainer rooms show 1/1 in the UI instead of 1/2.
    # The template must use item.effective_capacity instead of room.capacity.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
=======
    """
    ONE-CLICK ALLOCATION ORDER
    ─────────────────────────
    Step 1  Female students  ← highest priority, allocated first
    Step 2  Male   students
    Step 3  Trainers          ← only after ALL students are processed

    All three steps share the same in-memory `states` dict so every
    allocation is visible to subsequent iterations without extra DB reads.
    This is what prevents rooms from being scattered.
    """
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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

<<<<<<< HEAD
    states = _build_room_states()

=======
    # Build shared in-memory state — one DB read per room, done once.
    states = _build_room_states()

    # Pre-load date ranges for conflict checking — one DB read for all.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    allocations_by_room: dict[int, list] = {}
    for alloc in RoomAllocation.objects.filter(status='active').values(
        'room_id', 'checkin_date', 'checkout_date'
    ):
        allocations_by_room.setdefault(alloc['room_id'], []).append(alloc)

<<<<<<< HEAD
    student_allocated  = student_waitlisted = 0
    trainer_allocated  = trainer_waitlisted = 0
=======
    student_allocated  = 0
    student_waitlisted = 0
    trainer_allocated  = 0
    trainer_waitlisted = 0
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa

    female_students = [s for s in students if s['gender'] == 'female']
    male_students   = [s for s in students if s['gender'] == 'male']

<<<<<<< HEAD
=======
    # ═══════════════════════════════════════════════════
    # STEP 1 + 2 — Students (females first to get lower room numbers)
    # ═══════════════════════════════════════════════════
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    for student in female_students + male_students:
        gender   = student['gender']
        checkin  = student.get('checkin_date')
        checkout = student.get('checkout_date')
<<<<<<< HEAD
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

=======

        room_state = _find_room_for_student(
            gender, checkin, checkout, states, allocations_by_room
        )

        if room_state:
            RoomAllocation.objects.create(
                room=room_state.room,
                person_type='student',
                student_id=student['id'],
                student_name=student['name'],
                gender=gender,
                bed_number=room_state.occupied + 1,
                checkin_date=checkin,
                checkout_date=checkout,
                status='active',
            )
            # Mutate in-memory state — no DB re-read needed.
            room_state.add_occupant(gender, 'student')
            allocations_by_room.setdefault(room_state.room.pk, []).append({
                'room_id': room_state.room.pk,
                'checkin_date': checkin,
                'checkout_date': checkout,
            })
            student_allocated += 1
        else:
            WaitingList.objects.create(
                person_type='student',
                person_id=student['id'],
                person_name=student['name'],
                gender=gender,
                checkin_date=checkin,
                checkout_date=checkout,
                status='waiting',
            )
            student_waitlisted += 1

    # ═══════════════════════════════════════════════════
    # STEP 3 — Trainers (only after all students)
    # ═══════════════════════════════════════════════════
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    for trainer in trainers:
        gender   = trainer['gender']
        checkin  = trainer.get('checkin_date')
        checkout = trainer.get('checkout_date')
<<<<<<< HEAD
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

=======

        room_state = _find_room_for_trainer(
            gender, checkin, checkout, states, allocations_by_room
        )

        if room_state:
            RoomAllocation.objects.create(
                room=room_state.room,
                person_type='trainer',
                student_id=trainer['id'],
                student_name=trainer['name'],
                gender=gender,
                bed_number=1,
                checkin_date=checkin,
                checkout_date=checkout,
                status='active',
            )
            room_state.add_occupant(gender, 'trainer')
            allocations_by_room.setdefault(room_state.room.pk, []).append({
                'room_id': room_state.room.pk,
                'checkin_date': checkin,
                'checkout_date': checkout,
            })
            trainer_allocated += 1
        else:
            WaitingList.objects.create(
                person_type='trainer',
                person_id=trainer['id'],
                person_name=trainer['name'],
                gender=gender,
                checkin_date=checkin,
                checkout_date=checkout,
                status='waiting',
            )
            trainer_waitlisted += 1

    # Persist correct room status to DB for every room that was touched.
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    modified_pks = {s.room.pk for s in states.values() if s.occupied > 0}
    for room in Room.objects.filter(pk__in=modified_pks):
        _recalculate_room(room)

    if student_allocated == 0 and trainer_allocated == 0 \
            and student_waitlisted == 0 and trainer_waitlisted == 0:
<<<<<<< HEAD
        messages.info(request, "No pending students or trainers to allocate.")
    else:
        messages.success(
            request,
            f"Allocation complete — "
            f"Students: {student_allocated} allocated, {student_waitlisted} waitlisted | "
            f"Trainers: {trainer_allocated} allocated, {trainer_waitlisted} waitlisted"
        )
=======
        messages.info(request, "ℹ️ No pending students or trainers to allocate.")
    else:
        messages.success(
            request,
            f"✅ Allocation complete — "
            f"Students: {student_allocated} allocated, {student_waitlisted} waitlisted | "
            f"Trainers: {trainer_allocated} allocated, {trainer_waitlisted} waitlisted"
        )

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
    messages.success(request, f"{allocation.student_name} removed successfully.")
=======
    messages.success(request, f"✅ {allocation.student_name} removed successfully.")
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    return redirect('hostelmgmt:room_allocation')


@require_POST
def toggle_maintenance(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if room.status == 'maintenance':
<<<<<<< HEAD
        _recalculate_room(room)
        messages.success(request, f"Room {room.room_number} reactivated.")
    else:
        room.status = 'maintenance'
        room.save()
        messages.warning(request, f"Room {room.room_number} set to maintenance.")
=======
        _recalculate_room(room)   # restore from real allocations
        messages.success(request, f"✅ Room {room.room_number} reactivated.")
    else:
        room.status = 'maintenance'
        room.save()
        messages.warning(request, f"🔧 Room {room.room_number} set to maintenance.")
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
=======

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
=======

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    return render(request, 'hostelmgmt/room_transfer.html', {
        'rooms_data': rooms_data,
        'transfers':  transfers,
    })


# ═════════════════════════════════════════════════════════════
# DRAG & DROP TRANSFER
# ═════════════════════════════════════════════════════════════

@require_POST
def drag_drop_transfer(request):
<<<<<<< HEAD
=======
    """
    Validates and executes a drag-and-drop room transfer.

    FIX — Transfer history:
        The `reason` field is now written as a full sentence:
            "Anjali Sharma moved to Room 5 with Priya Nair"
        instead of the generic "Drag & Drop Transfer".
        The template should display {{ t.reason }} in the history column
        (see room_transfer.html update below).
    """
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    try:
        data          = json.loads(request.body)
        allocation_id = int(data.get('allocation_id'))
        to_room_id    = int(data.get('to_room_id'))
    except (TypeError, ValueError, KeyError):
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    allocation = get_object_or_404(RoomAllocation, pk=allocation_id, status='active')
    to_room    = get_object_or_404(Room, pk=to_room_id)
    from_room  = allocation.room

<<<<<<< HEAD
    if from_room.room_id == to_room.room_id:
        return JsonResponse({'success': False, 'message': 'Source and destination are the same room.'})
=======
    # ── Validation ────────────────────────────────────────────────────────
    if from_room.room_id == to_room.room_id:
        return JsonResponse({'success': False, 'message': 'Source and destination are the same room.'})

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
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
<<<<<<< HEAD
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
=======

    trainer_in_dest = active_in_dest.filter(person_type='trainer').exists()
    if trainer_in_dest:
        return JsonResponse({'success': False, 'message': 'Trainer room is private — transfer blocked.'})

    if allocation.person_type == 'trainer' and active_count > 0:
        return JsonResponse({'success': False, 'message': 'Trainer requires an empty room.'})

    # ── Rich history message ───────────────────────────────────────────────
    existing_names = _room_occupant_names(to_room)
    if existing_names:
        reason = (
            f"{allocation.student_name} moved to Room {to_room.room_number} "
            f"with {existing_names}"
        )
    else:
        reason = f"{allocation.student_name} moved to Room {to_room.room_number} (empty room)"

    # ── Execute transfer ───────────────────────────────────────────────────
    RoomTransfer.objects.create(
        student_id=allocation.student_id,
        student_name=allocation.student_name,
        from_room=from_room,
        to_room=to_room,
        reason=reason,
        status='approved',
    )

    allocation.room       = to_room
    allocation.bed_number = active_count + 1
    allocation.save()

>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    _recalculate_room(from_room)
    _recalculate_room(to_room)

    return JsonResponse({'success': True, 'message': reason})


# ═════════════════════════════════════════════════════════════
<<<<<<< HEAD
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
=======
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
# VISITORS
# ═════════════════════════════════════════════════════════════

def visitors(request):
    visitor_list = Visitor.objects.all().order_by('-visitor_id')[:30]
    return render(request, 'hostelmgmt/visitors.html', {'visitor_list': visitor_list})


def book_gate_pass(request):
    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            form.save()
<<<<<<< HEAD
            messages.success(request, 'Gate pass booked successfully.')
=======
            messages.success(request, '✅ Gate pass booked successfully.')
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
            return redirect('hostelmgmt:visitors')
    else:
        form = VisitorForm()
    return render(request, 'hostelmgmt/book_gate_pass.html', {'form': form})


# ═════════════════════════════════════════════════════════════
# COMPLAINTS
# ═════════════════════════════════════════════════════════════

def complaints(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            form.save()
<<<<<<< HEAD
            messages.success(request, 'Complaint submitted.')
            return redirect('hostelmgmt:complaints')
    else:
        form = ComplaintForm()
    complaint_list = (
        Complaint.objects.all().select_related('room').order_by('-complaint_id')[:30]
=======
            messages.success(request, '✅ Complaint submitted.')
            return redirect('hostelmgmt:complaints')
    else:
        form = ComplaintForm()

    complaint_list = (
        Complaint.objects.all()
        .select_related('room')
        .order_by('-complaint_id')[:30]
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    )
    return render(request, 'hostelmgmt/complaints.html', {
        'form':             form,
        'all_rooms':        Room.objects.all(),
        'complaint_list':   complaint_list,
        'open_count':       Complaint.objects.filter(status='open').count(),
        'inprogress_count': Complaint.objects.filter(status='in_progress').count(),
        'resolved_count':   Complaint.objects.filter(status='resolved').count(),
    })


# ═════════════════════════════════════════════════════════════
# MAINTENANCE
# ═════════════════════════════════════════════════════════════

def maintenance(request):
    rooms = (
        Room.objects.all()
        .annotate(room_no_int=Cast('room_number', IntegerField()))
        .order_by('room_no_int')
    )
    maintenance_requests = (
<<<<<<< HEAD
        MaintenanceRequest.objects.all().select_related('room').order_by('-request_id')[:20]
=======
        MaintenanceRequest.objects.all()
        .select_related('room')
        .order_by('-request_id')[:20]
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    )
    return render(request, 'hostelmgmt/maintenance.html', {
        'rooms':               rooms,
        'total':               rooms.count(),
        'available':           rooms.filter(status='available').count(),
        'full':                rooms.filter(status='full').count(),
        'under_maintenance':   rooms.filter(status='maintenance').count(),
        'maintenance_requests': maintenance_requests,
    })


# ═════════════════════════════════════════════════════════════
<<<<<<< HEAD
# REPORTS  (updated to include checkout stats)
# ═════════════════════════════════════════════════════════════

def reports(request):
    today        = date.today()
    allocations  = (
        RoomAllocation.objects.filter(status='active')
        .select_related('room').order_by('room__room_number')
    )
    waiting_list = WaitingList.objects.filter(status='waiting').order_by('added_on')
    room_wise    = (
        Room.objects.all()
        .annotate(room_no_int=Cast('room_number', IntegerField()))
        .order_by('room_no_int')
    )

    # Security checkout stats for the reports page
    checked_out_all  = RoomAllocation.objects.filter(
        status='vacated', actual_checkout_time__isnull=False
    )
    checked_out_today = checked_out_all.filter(actual_checkout_time__date=today)

    # Overdue: still active but planned checkout_date already passed
    overdue_count = RoomAllocation.objects.filter(
        status='active',
        actual_checkout_time__isnull=True,
        checkout_date__lt=today,
    ).count()
=======
# REPORTS
# ═════════════════════════════════════════════════════════════
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa

def reports(request):
    allocations  = (
        RoomAllocation.objects.filter(status='active')
        .select_related('room')
        .order_by('room__room_number')
    )
    waiting_list = WaitingList.objects.filter(status='waiting').order_by('added_on')
    room_wise    = (
        Room.objects.all()
        .annotate(room_no_int=Cast('room_number', IntegerField()))
        .order_by('room_no_int')
    )
    return render(request, 'hostelmgmt/reports.html', {
<<<<<<< HEAD
        'total_allocated':      allocations.count(),
        'total_visitors':       Visitor.objects.count(),
        'open_complaints':      Complaint.objects.filter(status='open').count(),
        'resolved_complaints':  Complaint.objects.filter(status='resolved').count(),
        'available_rooms':      Room.objects.filter(status='available').count(),
        'full_rooms':           Room.objects.filter(status='full').count(),
        'waiting_count':        waiting_list.count(),
        'room_wise':            room_wise,
        'allocations':          allocations,
        'waiting_list':         waiting_list,
        # Checkout stats
        'total_checked_out':    checked_out_all.count(),
        'checked_out_today':    checked_out_today.count(),
        'overdue_count':        overdue_count,
        'recent_checkouts':     checked_out_all.select_related('room').order_by('-actual_checkout_time')[:20],
=======
        'total_allocated':     allocations.count(),
        'total_visitors':      Visitor.objects.count(),
        'open_complaints':     Complaint.objects.filter(status='open').count(),
        'resolved_complaints': Complaint.objects.filter(status='resolved').count(),
        'available_rooms':     Room.objects.filter(status='available').count(),
        'full_rooms':          Room.objects.filter(status='full').count(),
        'waiting_count':       waiting_list.count(),
        'room_wise':           room_wise,
        'allocations':         allocations,
        'waiting_list':        waiting_list,
>>>>>>> b8b93250895fbd030f0735b4c9bc8d219420f9fa
    })