from django.urls import path

from .views import (
    availability,
    certification_create,
    certification_delete,
    certification_update,
    dashboard,
    trainer_create,
    trainer_delete,
    trainer_detail,
    trainer_list,
    trainer_skill_create,
    trainer_skill_delete,
    trainer_skill_update,
    trainer_update,
)

app_name = "trainers"

urlpatterns = [
    path("", trainer_list, name="list"),
    path("create/", trainer_create, name="create"),
    path("dashboard/", dashboard, name="dashboard"),
    path("availability/", availability, name="availability"),
    path("<int:pk>/", trainer_detail, name="detail"),
    path("<int:pk>/edit/", trainer_update, name="edit"),
    path("<int:pk>/delete/", trainer_delete, name="delete"),
    path("skills/create/", trainer_skill_create, name="skill-create"),
    path("skills/<int:pk>/edit/", trainer_skill_update, name="skill-edit"),
    path("skills/<int:pk>/delete/", trainer_skill_delete, name="skill-delete"),
    path("certifications/create/", certification_create, name="cert-create"),
    path("certifications/<int:pk>/edit/", certification_update, name="cert-edit"),
    path("certifications/<int:pk>/delete/", certification_delete, name="cert-delete"),
]
