from django.contrib import admin

from .models import Assessment, AssessmentResult


for model in [Assessment, AssessmentResult]:
    admin.site.register(model)
