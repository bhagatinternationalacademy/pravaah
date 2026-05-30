from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        'billing/',
        include('billingmgmt.urls')
    ),
]
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('billing/', include('billingmgmt.urls')),

    path('accounts/', include('django.contrib.auth.urls')),
]