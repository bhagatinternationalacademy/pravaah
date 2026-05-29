from django.urls import path

from .views import attendance_report, assessments_report, batches_report, certificates_report, export_csv, index, students_report, trainers_report

app_name = "reports"

urlpatterns = [
    path("", index, name="index"),
    path("students/", students_report, name="students"),
    path("trainers/", trainers_report, name="trainers"),
    path("attendance/", attendance_report, name="attendance"),
    path("certificates/", certificates_report, name="certificates"),
    path("assessments/", assessments_report, name="assessments"),
    path("batches/", batches_report, name="batches"),
    path("export/<str:kind>/", export_csv, name="export"),
]
