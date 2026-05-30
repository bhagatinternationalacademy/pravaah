"""
URL configuration for pravaah project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- Django Central Administrative Panel Portal ---
    path('admin/', admin.site.urls),
    
    # --- Central User Management & Portal Module Routing Hub ---
    # Mounted at root to flawlessly match internal app-level pathing definitions
    path('', include('usermgmt.urls')),

    # --- Trainer Management & Billing Module ---
    path('billing/', include('billingmgmt.urls')),
    
    # --- Proposal & Marketing Approvals Module ---
    path('proposals/', include('proposalmgmt.urls')),
]

# --- Media Uploads Asset Streamer Routing ---
# Safely exposes and handles uploaded file pathways when testing locally 
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
