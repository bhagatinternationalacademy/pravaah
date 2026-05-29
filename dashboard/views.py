# =============================================================
# PRAVAAH ERP - Shared Services Dashboard
# File: dashboard/views.py
# Purpose: Dashboard + Authentication Views
# =============================================================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q
from hostelmgmt.models import RoomAllocation, Room, Complaint, Hostel


# ── LOGIN ─────────────────────────────────────────────────────
def login_view(request):

    # ----------------------------------------------------------
    # Dummy Login Logic (temporary)
    # Later replace with Django authentication
    # ----------------------------------------------------------

    if request.method == 'POST':

        username = request.POST.get('username')
        role = request.POST.get('role')

        # Dummy session storage
        request.session['username'] = username
        request.session['role'] = role

        messages.success(
            request,
            f'✅ Welcome {username}! Login successful.'
        )

        return redirect('dashboard:main')

    return render(request, 'dashboard/login.html')


# ── LOGOUT ────────────────────────────────────────────────────
def logout_view(request):

    request.session.flush()

    messages.success(
        request,
        '✅ Logged out successfully.'
    )

    return redirect('dashboard:login')


# ── MAIN DASHBOARD ────────────────────────────────────────────
def dashboard_view(request):

    # ----------------------------------------------------------
    # Session Check
    # ----------------------------------------------------------

    username = request.session.get('username')
    role = request.session.get('role')

    if not username:
        messages.error(
            request,
            '❌ Please login first.'
        )
        return redirect('dashboard:login')

    # ----------------------------------------------------------
    # Role Display Mapping
    # ----------------------------------------------------------

    role_display_map = {
        'admin': 'Administrator',
        'trainer': 'Trainer',
        'student': 'Student',
    }

    role_display = role_display_map.get(
        role,
        'User'
    )

    # ----------------------------------------------------------
    # Dashboard Cards
    # ----------------------------------------------------------

    all_cards = [

        {
            'id': 1,
            'title': 'User Management',
            'description': 'Manage users, permissions and roles.',
            'icon': 'fa-users-cog',
            'badge': 'Admin',
            'url': '/user-overview/',
            'color': 'blue',
            'roles': ['admin'],
        },

        {
            'id': 2,
            'title': 'Trainer Management',
            'description': 'Manage trainers and assignments.',
            'icon': 'fa-chalkboard-teacher',
            'badge': 'Core',
            'url': '/trainer-overview/',
            'color': 'green',
            'roles': ['admin', 'trainer'],
        },

        {
            'id': 3,
            'title': 'Student Management',
            'description': 'Track student records and attendance.',
            'icon': 'fa-user-graduate',
            'badge': 'Academic',
            'url': '/student-overview/',
            'color': 'purple',
            'roles': ['admin', 'trainer'],
        },

        {
            'id': 4,
            'title': 'Course Management',
            'description': 'Programs, batches and sessions.',
            'icon': 'fa-book-open',
            'badge': 'Learning',
            'url': '/course-overview/',
            'color': 'orange',
            'roles': ['admin', 'trainer', 'student'],
        },

        {
            'id': 5,
            'title': 'Hostel Management',
            'description': 'Room allocation and complaints.',
            'icon': 'fa-building',
            'badge': 'Facilities',
            'url': '/hostel-overview/',
            'color': 'red',
            'roles': ['admin'],
        },

    ]

    # ----------------------------------------------------------
    # Filter cards by role
    # ----------------------------------------------------------

    cards = [
        card for card in all_cards
        if role in card['roles']
    ]

    # ----------------------------------------------------------
    # Statistics (from hostel data)
    # ----------------------------------------------------------

    # Get total students from room allocations
    total_students = RoomAllocation.objects.filter(
        status='active'
    ).count()

    # Get active hostel rooms
    total_rooms = Room.objects.filter(
        status='available'
    ).count()

    # Get pending complaints
    pending_complaints = Complaint.objects.filter(
        status__in=['open', 'in_progress']
    ).count()

    # Get total hostels
    total_hostels = Hostel.objects.filter(
        status='active'
    ).count()

    stats = [

        {
            'label': 'Students',
            'value': total_students,
            'icon': 'fa-user-graduate',
            'color': 'blue',
        },

        {
            'label': 'Available Rooms',
            'value': total_rooms,
            'icon': 'fa-door-open',
            'color': 'green',
        },

        {
            'label': 'Pending Issues',
            'value': pending_complaints,
            'icon': 'fa-exclamation-triangle',
            'color': 'orange',
        },

        {
            'label': 'Active Hostels',
            'value': total_hostels,
            'icon': 'fa-building',
            'color': 'red',
        },

    ]

    # ----------------------------------------------------------
    # Context
    # ----------------------------------------------------------

    context = {

        'full_name': username,
        'role': role,
        'role_display': role_display,

        'cards': cards,
        'stats': stats,

        'total_cards': len(cards),
    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )


# ── STUDENT DASHBOARD ─────────────────────────────────────────
def student_dashboard_view(request):
    """Student management dashboard - displays student/hostel allocation data"""

    # ----------------------------------------------------------
    # Session Check
    # ----------------------------------------------------------

    username = request.session.get('username')
    role = request.session.get('role')

    if not username:
        messages.error(request, '❌ Please login first.')
        return redirect('dashboard:login')

    # ----------------------------------------------------------
    # Get Student Data from RoomAllocation
    # ----------------------------------------------------------

    all_students = RoomAllocation.objects.filter(status='active')
    total_students = all_students.count()

    # Gender breakdown
    male_students = all_students.filter(gender='male').count()
    female_students = all_students.filter(gender='female').count()

    # Room occupancy stats
    total_rooms = Room.objects.all().count()
    available_rooms = Room.objects.filter(status='available').count()
    full_rooms = Room.objects.filter(status='full').count()
    maintenance_rooms = Room.objects.filter(status='maintenance').count()

    # Hostel-wise student distribution
    hostels_data = []
    for hostel in Hostel.objects.filter(status='active'):
        hostel_count = RoomAllocation.objects.filter(
            status='active',
            room__floor__block__hostel=hostel
        ).count()
        hostels_data.append({
            'name': hostel.hostel_name,
            'count': hostel_count,
        })

    # Complaint statistics
    total_complaints = Complaint.objects.all().count()
    open_complaints = Complaint.objects.filter(status='open').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()

    # Complaint types breakdown
    complaint_types = Complaint.objects.values('complaint_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Recent students (allocations)
    recent_students = RoomAllocation.objects.filter(
        status='active'
    ).order_by('-allocation_date')[:5]

    # Recent complaints
    recent_complaints = Complaint.objects.all().order_by('-complaint_date')[:5]

    # ----------------------------------------------------------
    # Dashboard Cards
    # ----------------------------------------------------------

    stats = [
        {
            'label': 'Total Students',
            'value': total_students,
            'icon': 'fa-user-graduate',
            'color': 'blue',
        },
        {
            'label': 'Male Students',
            'value': male_students,
            'icon': 'fa-mars',
            'color': 'purple',
        },
        {
            'label': 'Female Students',
            'value': female_students,
            'icon': 'fa-venus',
            'color': 'pink',
        },
        {
            'label': 'Pending Complaints',
            'value': open_complaints,
            'icon': 'fa-exclamation-circle',
            'color': 'orange',
        },
    ]

    # Room status breakdown
    room_status = [
        {'status': 'Available', 'count': available_rooms, 'color': 'green'},
        {'status': 'Full', 'count': full_rooms, 'color': 'red'},
        {'status': 'Maintenance', 'count': maintenance_rooms, 'color': 'orange'},
    ]

    # Complaint status breakdown
    complaint_status = [
        {'status': 'Open', 'count': open_complaints, 'color': 'red'},
        {'status': 'In Progress', 'count': in_progress_complaints, 'color': 'orange'},
        {'status': 'Resolved', 'count': resolved_complaints, 'color': 'green'},
    ]

    context = {
        'full_name': username,
        'role': role,
        'role_display': 'Administrator' if role == 'admin' else 'Trainer',

        # Stats
        'stats': stats,
        'total_students': total_students,
        'male_students': male_students,
        'female_students': female_students,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,

        # Breakdowns
        'room_status': room_status,
        'complaint_status': complaint_status,
        'hostels_data': hostels_data,
        'complaint_types': list(complaint_types),

        # Recent data
        'recent_students': recent_students,
        'recent_complaints': recent_complaints,

        # Summary
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
    }

    return render(
        request,
        'dashboard/student_dashboard.html',
        context
    )

def hostel_overview(request):

    context = {
        "total_rooms": 120,
        "occupied_rooms": 98,
        "pending_complaints": 7,
        "maintenance_requests": 4,
    
    }

    return render(request,"dashboard/hostel_overview.html", context)

def user_overview(request):

    context = {
        'total_users': 120,
        'active_users': 95,
        'inactive_users': 25,
    }

    return render(
        request,
        'dashboard/user_overview.html',
        context
    )

def trainer_overview(request):

    context = {
        'total_trainers': 18,
        'active_trainers': 15,
        'assigned_batches': 12,
    }

    return render(
        request,
        'dashboard/trainer_overview.html',
        context
    )

def student_overview(request):

    context = {
        'total_students': 420,
        'active_students': 390,
        'attendance_percentage': 89,
    }

    return render(
        request,
        'dashboard/student_overview.html',
        context
    )

def course_overview(request):

    context = {
        'total_courses': 14,
        'active_batches': 9,
        'completed_courses': 5,
    }

    return render(
        request,
        'dashboard/course_overview.html',
        context
    )

def backup_restore_view(request):

    return render(
        request,
        'dashboard/backup_restore.html'
    )