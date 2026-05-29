from django.urls import path

from participantmgmt import views

app_name = 'participantmgmt'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('api/documents/upload/', views.document_upload_api, name='document_upload_api'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/register/documents/', views.register_documents_view, name='register_documents'),
    path('accounts/register/course/', views.register_course_view, name='register_course'),
    path('accounts/register/payment/', views.register_payment_view, name='register_payment'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('dashboard/', views.home, name='home'),
    path('students/profile/', views.profile_view, name='profile'),
    path('students/profile/edit/', views.profile_edit, name='profile_edit'),
    path('students/attendance/', views.attendance_view, name='attendance'),
    path('students/assessment/', views.assessment_view, name='assessment'),
    path('students/results/', views.results_view, name='results'),
]