from django.urls import path
from . import views
from . import students_views
from . import history_views

app_name = 'trainers'

urlpatterns = [
    path('', views.trainer_list, name='list'),
    path('add/', views.trainer_add, name='add'),
    path('profile/', views.trainer_profile, name='profile'),
    path('profile/edit/', views.trainer_profile_edit, name='profile_edit'),

    # Students & Attendance
    path('students/', students_views.students_list, name='students'),
    path('students/attendance/<int:batch_id>/', students_views.attendance, name='attendance'),
    path('students/attendance/history/<int:batch_id>/', history_views.attendance_history, name='attendance_history'),

    # Registration & approval workflow
    path('register/', views.trainer_register, name='register'),
    path('register/submitted/', views.registration_submitted, name='registration_submitted'),
    path('pending/', views.pending_trainers, name='pending_list'),
    path('approve/<int:pk>/', views.approve_trainer, name='approve'),
    path('reject/<int:pk>/', views.reject_trainer, name='reject'),
    path('<int:pk>/', views.trainer_detail, name='detail'),
    path('edit/<int:pk>/', views.trainer_edit, name='edit'),
    path('delete/<int:pk>/', views.trainer_delete, name='delete'),
]
