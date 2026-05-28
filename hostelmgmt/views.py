from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (Room, RoomAllocation, RoomTransfer,
                     Visitor, Complaint, MaintenanceRequest)
from .forms import RoomAllocationForm, VisitorForm, ComplaintForm


# ── DASHBOARD ────────────────────────────────────────────────────────────────
def hostel_dashboard(request):
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(status='available').count()
    allocated_rooms = Room.objects.filter(status='full').count()
    total_complaints = Complaint.objects.filter(status='open').count()
    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'allocated_rooms': allocated_rooms,
        'total_complaints': total_complaints,
    }
    return render(request, 'hostelmgmt/dashboard.html', context)


# ── ROOM ALLOCATION ───────────────────────────────────────────────────────────
def room_allocation(request):
    if request.method == 'POST':
        form = RoomAllocationForm(request.POST)
        if form.is_valid():
            gender = form.cleaned_data['gender']

            # 1. Try a room that already matches the gender and has space
            room = Room.objects.filter(
                status='available',
                gender=gender
            ).first()

            # 2. Fall back: room with no gender assigned yet
            if not room:
                room = Room.objects.filter(
                    status='available',
                    gender__isnull=True
                ).first()

            if not room:
                messages.error(
                    request,
                    '❌ No available rooms for this gender. All rooms are currently full.'
                )
                return render(request, 'hostelmgmt/room_allocation.html', {
                    'form': form,
                    'allocations': RoomAllocation.objects.filter(
                        status='active').select_related('room')[:20]
                })

            # Save allocation
            allocation = form.save(commit=False)
            allocation.room = room
            allocation.bed_number = room.occupied + 1
            allocation.save()

            # Update room
            room.occupied += 1
            room.gender = gender
            if room.occupied >= room.capacity:
                room.status = 'full'
            room.save()

            messages.success(
                request,
                f'✅ Room {room.room_number} allocated to {allocation.student_name} successfully!'
            )
            return redirect('hostelmgmt:room_allocation')
    else:
        form = RoomAllocationForm()

    allocations = RoomAllocation.objects.filter(
        status='active'
    ).select_related('room').order_by('-allocation_id')[:20]

    return render(request, 'hostelmgmt/room_allocation.html', {
        'form': form,
        'allocations': allocations,
    })


# ── ROOM TRANSFER ─────────────────────────────────────────────────────────────
def room_transfer(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id', '').strip()
        from_room_id = request.POST.get('from_room')
        to_room_id = request.POST.get('to_room')
        reason = request.POST.get('reason', '').strip()

        errors = {}
        if not student_id:
            errors['student_id'] = 'Student ID is required.'
        if not from_room_id:
            errors['from_room'] = 'Please select current room.'
        if not to_room_id:
            errors['to_room'] = 'Please select requested room.'
        if from_room_id and to_room_id and from_room_id == to_room_id:
            errors['to_room'] = 'Current room and requested room cannot be the same.'
        if not reason:
            errors['reason'] = 'Please provide a reason.'

        if not errors:
            try:
                from_room = Room.objects.get(pk=from_room_id)
                to_room = Room.objects.get(pk=to_room_id)

                if not to_room.is_available():
                    messages.error(request, '❌ Requested room is already full. Please choose another room.')
                else:
                    # Create transfer record
                    transfer = RoomTransfer.objects.create(
                        student_id=student_id,
                        from_room=from_room,
                        to_room=to_room,
                        reason=reason,
                        status='approved',
                    )

                    # Adjust occupancy
                    from_room.occupied = max(0, from_room.occupied - 1)
                    if from_room.occupied == 0:
                        from_room.gender = None
                    if from_room.occupied < from_room.capacity:
                        from_room.status = 'available'
                    from_room.save()

                    to_room.occupied += 1
                    if to_room.occupied >= to_room.capacity:
                        to_room.status = 'full'
                    to_room.save()

                    messages.success(
                        request,
                        f'✅ Transfer approved! {student_id} moved from Room {from_room.room_number} to Room {to_room.room_number}.'
                    )
                    return redirect('hostelmgmt:room_transfer')

            except Room.DoesNotExist:
                messages.error(request, '❌ Invalid room selected.')

        all_rooms = Room.objects.all().select_related('floor')
        available_rooms = Room.objects.filter(status='available').select_related('floor')
        transfers = RoomTransfer.objects.all().select_related(
            'from_room', 'to_room').order_by('-transfer_id')[:20]
        return render(request, 'hostelmgmt/room_transfer.html', {
            'all_rooms': all_rooms,
            'available_rooms': available_rooms,
            'transfers': transfers,
            'errors': errors,
            'post_data': request.POST,
        })

    all_rooms = Room.objects.all().select_related('floor')
    available_rooms = Room.objects.filter(status='available').select_related('floor')
    transfers = RoomTransfer.objects.all().select_related(
        'from_room', 'to_room').order_by('-transfer_id')[:20]

    return render(request, 'hostelmgmt/room_transfer.html', {
        'all_rooms': all_rooms,
        'available_rooms': available_rooms,
        'transfers': transfers,
    })


# ── VISITORS ──────────────────────────────────────────────────────────────────
def visitors(request):
    visitor_list = Visitor.objects.all().order_by('-visitor_id')[:30]
    return render(request, 'hostelmgmt/visitors.html', {'visitor_list': visitor_list})


def book_gate_pass(request):
    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Gate pass booked successfully! Visitor has been registered.')
            return redirect('hostelmgmt:visitors')
        else:
            messages.error(request, '❌ Please fix the errors below.')
    else:
        form = VisitorForm()

    return render(request, 'hostelmgmt/book_gate_pass.html', {'form': form})


# ── COMPLAINTS ────────────────────────────────────────────────────────────────
def complaints(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Complaint submitted successfully! We will look into it.')
            return redirect('hostelmgmt:complaints')
        else:
            messages.error(request, '❌ Please fix the errors below.')
    else:
        form = ComplaintForm()

    all_rooms = Room.objects.all()
    complaint_list = Complaint.objects.all().select_related('room').order_by('-complaint_id')[:30]
    open_count = Complaint.objects.filter(status='open').count()
    inprogress_count = Complaint.objects.filter(status='in_progress').count()
    resolved_count = Complaint.objects.filter(status='resolved').count()

    return render(request, 'hostelmgmt/complaints.html', {
        'form': form,
        'all_rooms': all_rooms,
        'complaint_list': complaint_list,
        'open_count': open_count,
        'inprogress_count': inprogress_count,
        'resolved_count': resolved_count,
    })


# ── MAINTENANCE ───────────────────────────────────────────────────────────────
def maintenance(request):
    rooms = Room.objects.all().select_related('floor__block')
    total = rooms.count()
    available = rooms.filter(status='available').count()
    full = rooms.filter(status='full').count()
    under_maintenance = rooms.filter(status='maintenance').count()
    maintenance_requests = MaintenanceRequest.objects.all().select_related(
        'room').order_by('-request_id')[:20]

    return render(request, 'hostelmgmt/maintenance.html', {
        'rooms': rooms,
        'total': total,
        'available': available,
        'full': full,
        'under_maintenance': under_maintenance,
        'maintenance_requests': maintenance_requests,
    })


# ── REPORTS ───────────────────────────────────────────────────────────────────
def reports(request):
    total_allocated = RoomAllocation.objects.filter(status='active').count()
    total_visitors = Visitor.objects.count()
    open_complaints = Complaint.objects.filter(status='open').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    available_rooms = Room.objects.filter(status='available').count()
    full_rooms = Room.objects.filter(status='full').count()
    room_wise = Room.objects.all().select_related('floor').order_by('floor__floor_no', 'room_number')

    return render(request, 'hostelmgmt/reports.html', {
        'total_allocated': total_allocated,
        'total_visitors': total_visitors,
        'open_complaints': open_complaints,
        'resolved_complaints': resolved_complaints,
        'available_rooms': available_rooms,
        'full_rooms': full_rooms,
        'room_wise': room_wise,
    })