from django.urls import path
from . import views  # local views

app_name = 'usermgmt'

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('session-expired/', views.session_expired_view, name='session_expired'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email_view, name='verify_email_confirm'),
    path('logout/', views.logout_view, name='logout'),

    path('rbac/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('rbac/roles/', views.roles_list_view, name='roles_list'),
    path('rbac/roles/add/', views.role_form_view, name='role_add'),
    path('rbac/permissions/', views.permissions_list_view, name='permissions_list'),
    path('rbac/assign-role/', views.assign_role_view, name='assign_role'),
    path('rbac/assign-permissions/', views.assign_permissions_view, name='assign_permissions'),
    path('rbac/matrix/', views.permission_matrix_view, name='permission_matrix'),
]
