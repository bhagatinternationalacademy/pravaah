from django.urls import path
from .views import *

urlpatterns = [

    path(
        '',
        assessment_list,
        name='assessment_list'
    ),

    path(
        'create/',
        create_assessment,
        name='create_assessment'
    ),

    path(
    'edit/<int:id>/',
    edit_assessment,
    name='edit_assessment'
    ),

    path(
    'delete/<int:id>/',
    delete_assessment,
    name='delete_assessment'
    ),

]