from django.urls import path
from . import views

app_name = 'skills'

urlpatterns = [
    path('', views.skill_list, name='list'),
    path('add/', views.skill_add, name='add'),
    path('assign/', views.assign_skill, name='assign'),
]
