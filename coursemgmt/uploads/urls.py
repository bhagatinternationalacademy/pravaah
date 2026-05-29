from django.urls import path

from .views import upload_excel

app_name = "uploads"

urlpatterns = [
    path("", upload_excel, name="upload"),
]
