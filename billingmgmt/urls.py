"""
URL configuration for the Billing Management module.

All URL patterns are namespaced under ``billing`` (``app_name = 'billing'``).
Include these in the project-level ``urls.py`` with::

    path('billing/', include('billingmgmt.urls')),
"""

from django.urls import path

from . import views

app_name = 'billing'

urlpatterns = [
    # --- Dashboard ---
    path('', views.dashboard, name='dashboard'),

    # --- Trainer URLs ---
    path('upload/', views.upload_bill, name='upload_bill'),
    path('my-bills/', views.my_bills, name='my_bills'),

    # --- Accounts department URLs ---
    path('accounts/', views.accounts_pending_bills, name='accounts_pending'),
    path('accounts/approve/<int:pk>/', views.accounts_approve_bill, name='accounts_approve'),
    path('accounts/reject/<int:pk>/', views.accounts_reject_bill, name='accounts_reject'),

    # --- Trainer Admin URLs ---
    path('trainer-admin/', views.trainer_admin_bills, name='trainer_admin_bills'),
    path('trainer-admin/approve/<int:pk>/', views.trainer_admin_approve_bill, name='trainer_admin_approve'),
    path('trainer-admin/reject/<int:pk>/', views.trainer_admin_reject_bill, name='trainer_admin_reject'),

    # --- Notification URLs ---
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_read'),

    # --- Bill PDF preview ---
    path('bill/preview/<int:pk>/', views.bill_pdf_preview, name='bill_pdf_preview'),
]
