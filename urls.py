from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Root -> Login (make login the first page)
    
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),

    # Dashboard (moved)
    path('dashboard/', include('pravaah.dashboard.urls')),

    # Accounts
    path('accounts/', include('pravaah.accounts.urls')),

    # Trainers
    path('trainers/', include('pravaah.trainers.urls')),

    # Skills
    path('skills/', include('pravaah.skills.urls')),

    # Certifications
    path('certifications/', include('pravaah.certifications.urls')),

    # Reports
    path('reports/', include('pravaah.reports.urls')),

    # Assessment
    path('assessment/', include('pravaah.assessment.urls')),

    # Batch
    path('batch/', include('pravaah.batch.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    