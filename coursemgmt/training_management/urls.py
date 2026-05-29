from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from dashboard.views import landing

urlpatterns = [
    path("", landing, name="landing"),
    path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("programs/", include("programs.urls")),
    path("trainers/", include("trainers.urls")),
    path("students/", include("students.urls")),
    path("batches/", include("batches.urls")),
    path("attendance/", include("attendance.urls")),
    path("assessments/", include("assessments.urls")),
    path("certificates/", include("certificates.urls")),
    path("uploads/", include("uploads.urls")),
    path("reports/", include("reports.urls")),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
