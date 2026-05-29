# =============================================================
# PRAVAAH ERP - Shared Services Dashboard
# File: dashboard/urls.py
# Purpose: URL routing for the dashboard app
# =============================================================

from django.urls import path
from . import views

# Namespace: allows {% url 'dashboard:login' %} in templates
app_name = 'dashboard'

urlpatterns = [

    # ----------------------------------------------------------
    # Login / Logout
    # ----------------------------------------------------------
    path('',        views.login_view,     name='login'),    # /
    path('login/',  views.login_view,     name='login'),    # /login/
    path('logout/', views.logout_view,    name='logout'),   # /logout/

    # ----------------------------------------------------------
    # Main Shared Services Dashboard  (protected)
    # ----------------------------------------------------------
    path('dashboard/', views.dashboard_view, name='main'),  # /dashboard/
    
    # ----------------------------------------------------------
    # Student Management Dashboard (uses hostel student data)
    # ----------------------------------------------------------
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),  # /dashboard/student-dashboard/
    path('hostel-overview/', views.hostel_overview, name='hostel_overview'),
    path('user-overview/', views.user_overview, name='user_overview'),

    path('trainer-overview/', views.trainer_overview, name='trainer_overview'),

    path('student-overview/', views.student_overview, name='student_overview'),

    path('course-overview/', views.course_overview, name='course_overview'),

    path(
    'backup-restore/',
    views.backup_restore_view,
    name='backup_restore'
),
]


# =============================================================
# HOW TO INCLUDE THIS IN pravaah/urls.py
# =============================================================
#
# In your root urls.py (pravaah/urls.py), add:
#
#   from django.urls import path, include
#
#   urlpatterns = [
#       path('admin/', admin.site.urls),
#
#       # Shared Services Dashboard (entry point)
#       path('', include('dashboard.urls', namespace='dashboard')),
#
#       # -------------------------------------------------------
#       # Each team's independent dashboard (external routes)
#       # The dashboard app only REDIRECTS to these; it does NOT
#       # own them. Each team registers their own app here.
#       # -------------------------------------------------------
#       path('user-management/', include('usermgmt.urls')),
#       path('trainer/',         include('trainermgmt.urls')),
#       path('hostel/',          include('hostelmgmt.urls')),
#       path('student/',         include('participantmgmt.urls')),
#       path('course/',          include('coursemgmt.urls')),
#   ]
#
# =============================================================