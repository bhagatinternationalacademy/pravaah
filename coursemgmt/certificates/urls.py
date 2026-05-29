from django.urls import path

from .views import certificate_create, certificate_delete, certificate_list, certificate_update

app_name = "certificates"

urlpatterns = [
    path("", certificate_list, name="list"),
    path("create/", certificate_create, name="create"),
    path("<int:pk>/edit/", certificate_update, name="edit"),
    path("<int:pk>/delete/", certificate_delete, name="delete"),
]
