from django.urls import path
from . import views

app_name = 'batch'

urlpatterns = [
    path('', views.batch_list, name='list'),
    path('add/', views.batch_add, name='add'),
    path('<int:pk>/', views.batch_detail, name='detail'),
    path('edit/<int:pk>/', views.batch_edit, name='edit'),
    path('delete/<int:pk>/', views.batch_delete, name='delete'),
]
