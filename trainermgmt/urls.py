from django.urls import path
from . import views

app_name = 'trainermgmt'

urlpatterns = [
    path('dashboard/', views.accounts_dashboard_view, name='accounts_dashboard'),
    path('process-payment/<int:trainer_id>/', views.process_payment_view, name='process_payment'),
    path('payment-history/', views.payment_history_view, name='payment_history'),
]
