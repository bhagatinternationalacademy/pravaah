from django.urls import path
from . import views

app_name = 'hostelmgmt'

urlpatterns = [
    path('', views.hostel_dashboard, name='dashboard'),
    path('allocation/', views.room_allocation, name='room_allocation'),
    path('transfer/', views.room_transfer, name='room_transfer'),
    path('visitors/', views.visitors, name='visitors'),
    path('visitors/book/', views.book_gate_pass, name='book_gate_pass'),
    path('complaints/', views.complaints, name='complaints'),
    path('maintenance/', views.maintenance, name='maintenance'),
    path('reports/', views.reports, name='reports'),
]