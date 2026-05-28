from django.urls import path
from . import views

app_name = 'certifications'

urlpatterns = [
    path('', views.certification_list, name='list'),
    path('add/', views.certification_add, name='add'),
]
