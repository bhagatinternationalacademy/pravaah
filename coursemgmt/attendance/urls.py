from django.urls import path

from .views import attendance_batch_sessions_api, attendance_bulk_export, attendance_bulk_mark, attendance_create, attendance_delete, attendance_list, attendance_update

app_name = "attendance"

urlpatterns = [
    path("", attendance_list, name="list"),
    path("create/", attendance_create, name="create"),
    path("bulk/", attendance_bulk_mark, name="bulk-mark"),
    path("bulk/sessions/", attendance_batch_sessions_api, name="bulk-sessions"),
    path("bulk/export/<str:kind>/", attendance_bulk_export, name="bulk-export"),
    path("<int:pk>/edit/", attendance_update, name="edit"),
    path("<int:pk>/delete/", attendance_delete, name="delete"),
]
