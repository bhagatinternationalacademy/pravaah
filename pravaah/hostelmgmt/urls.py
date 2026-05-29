from django.urls import path
from . import views

app_name = 'hostelmgmt'

urlpatterns = [
    path('', views.hostel_dashboard, name='dashboard'),

    # Room Allocation
    path('allocation/', views.room_allocation, name='room_allocation'),
    path('allocation/auto/', views.auto_allocate, name='auto_allocate'),
    path('allocation/remove/<int:allocation_id>/', views.remove_occupant, name='remove_occupant'),
    path('allocation/maintenance/<int:room_id>/', views.toggle_maintenance, name='toggle_maintenance'),

    # Room Transfer (drag & drop)
    path('transfer/', views.room_transfer, name='room_transfer'),
    path('transfer/drag-drop/', views.drag_drop_transfer, name='drag_drop_transfer'),

    # Visitors
    path('visitors/', views.visitors, name='visitors'),
    path('visitors/book/', views.book_gate_pass, name='book_gate_pass'),

    # Other modules
    path('complaints/', views.complaints, name='complaints'),
    path('maintenance/', views.maintenance, name='maintenance'),
    path('reports/', views.reports, name='reports'),

    # Security / Physical Checkout
    path('security/', views.security, name='security'),
    path('security/checkout/<int:allocation_id>/', views.security_checkout, name='security_checkout'),
    path('security/checkout/bulk/', views.security_checkout_bulk, name='security_checkout_bulk'),
]