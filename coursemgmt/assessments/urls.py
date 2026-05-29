from django.urls import path

from .views import (
    assessment_create,
    assessment_delete,
    assessment_list,
    assessment_update,
    result_create,
    result_delete,
    result_export_view,
    result_list,
    result_update,
)

app_name = "assessments"

urlpatterns = [
    path("", assessment_list, name="list"),
    path("create/", assessment_create, name="create"),
    path("<int:pk>/edit/", assessment_update, name="edit"),
    path("<int:pk>/delete/", assessment_delete, name="delete"),
    path("results/", result_list, name="results"),
    path("results/create/", result_create, name="result-create"),
    path("results/export/<str:kind>/", result_export_view, name="result-export"),
    path("results/<int:pk>/edit/", result_update, name="result-edit"),
    path("results/<int:pk>/delete/", result_delete, name="result-delete"),
]
