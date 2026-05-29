from django.urls import path

from .views import (
    dashboard,
    student_create,
    student_delete,
    student_detail,
    student_guardian_create,
    student_guardian_delete,
    student_guardian_update,
    student_list,
    student_update,
    assessment_results,
    export_marks,
)

app_name = "students"

urlpatterns = [
    path("", student_list, name="list"),
    path("create/", student_create, name="create"),
    path("dashboard/", dashboard, name="dashboard"),
    path("assessment-results/", assessment_results, name="assessment-results"),
    path("export-marks/", export_marks, name="export-marks"),
    path("<int:pk>/", student_detail, name="detail"),
    path("<int:pk>/edit/", student_update, name="edit"),
    path("<int:pk>/delete/", student_delete, name="delete"),
    path("guardians/create/", student_guardian_create, name="guardian-create"),
    path("guardians/<int:pk>/edit/", student_guardian_update, name="guardian-edit"),
    path("guardians/<int:pk>/delete/", student_guardian_delete, name="guardian-delete"),
]
