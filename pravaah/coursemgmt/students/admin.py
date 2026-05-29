from django.contrib import admin

from .models import Student, StudentGuardian


for model in [Student, StudentGuardian]:
    admin.site.register(model)
