from django.urls import path

from .views import (
    availability,
    certification_create,
    certification_delete,
    certification_update,
    dashboard,
    trainer_delete,
    trainer_detail,
    trainer_list,
    trainer_skill_create,
    trainer_skill_delete,
    trainer_skill_update,
    program_trainer_list,
    program_trainer_create,
    program_trainer_update,
    program_trainer_delete,
    course_trainer_list,
    course_trainer_create,
    course_trainer_update,
    course_trainer_delete,
)

app_name = "trainers"

urlpatterns = [
    path("", trainer_list, name="list"),
    path("dashboard/", dashboard, name="dashboard"),
    path("availability/", availability, name="availability"),
    path("<int:pk>/", trainer_detail, name="detail"),
    path("<int:pk>/delete/", trainer_delete, name="delete"),
    path("skills/create/", trainer_skill_create, name="skill-create"),
    path("skills/<int:pk>/edit/", trainer_skill_update, name="skill-edit"),
    path("skills/<int:pk>/delete/", trainer_skill_delete, name="skill-delete"),
    path("certifications/create/", certification_create, name="cert-create"),
    path("certifications/<int:pk>/edit/", certification_update, name="cert-edit"),
    path("certifications/<int:pk>/delete/", certification_delete, name="cert-delete"),
    path("programs/", program_trainer_list, name="program-trainer-list"),
    path("programs/create/", program_trainer_create, name="program-trainer-create"),
    path("programs/<int:pk>/edit/", program_trainer_update, name="program-trainer-edit"),
    path("programs/<int:pk>/delete/", program_trainer_delete, name="program-trainer-delete"),
    path("courses/", course_trainer_list, name="course-trainer-list"),
    path("courses/create/", course_trainer_create, name="course-trainer-create"),
    path("courses/<int:pk>/edit/", course_trainer_update, name="course-trainer-edit"),
    path("courses/<int:pk>/delete/", course_trainer_delete, name="course-trainer-delete"),
]
