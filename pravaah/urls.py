"""
URL configuration for pravaah project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from pravaah import views as pravaah_views

urlpatterns = [
    # --- Django Central Administrative Panel Portal ---
    path('admin/', admin.site.urls),
    
    # --- Pravaah App Core Routes ---
    path('', pravaah_views.landing_page, name='pravaah_landing'),
    path('future-proposals/', pravaah_views.future_proposals_list, name='pravaah_future_proposals'),
    path('future-proposals/add/', pravaah_views.add_proposal, name='pravaah_add_proposal'),
    path('gate-0/', pravaah_views.gate_zero_form, name='pravaah_gate_zero'),
    path('gate-0/<int:proposal_id>/', pravaah_views.gate_zero_form, name='pravaah_gate_zero_proposal'),
    path('gate-approval/', pravaah_views.gate_approval_form, name='pravaah_gate_approval'),
    path('gate-approval/<int:proposal_id>/', pravaah_views.gate_approval_form, name='pravaah_gate_approval_proposal'),
    
    # --- Marketing Approval Workflows ---
    path('marketing/queue/', pravaah_views.marketing_queue, name='pravaah_marketing_queue'),
    path('marketing/approve/<int:approval_id>/', pravaah_views.approve_gate_approval, name='pravaah_approve_gate_approval'),
    path('marketing/reject/<int:approval_id>/', pravaah_views.reject_gate_approval, name='pravaah_reject_gate_approval'),
    
    # --- Central User Management & Portal Module Routing Hub ---
    # Mounted at root to flawlessly match internal app-level pathing definitions
    path('', include('usermgmt.urls')),

    # --- Trainer Management & Accounts Module ---
    path('trainers/', include('trainermgmt.urls')),
]

# --- Media Uploads Asset Streamer Routing ---
# Safely exposes and handles uploaded file pathways when testing locally 
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
