from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.trainer_reports, name='trainer_reports'),
    path('export/trainers/', views.export_trainers_csv, name='export_trainers_csv'),
    path('export/certifications/', views.export_certifications_csv, name='export_certifications_csv'),
]
