from django.contrib import admin

from .models import Certification, Trainer, TrainerSkill


for model in [Trainer, TrainerSkill, Certification]:
    admin.site.register(model)
