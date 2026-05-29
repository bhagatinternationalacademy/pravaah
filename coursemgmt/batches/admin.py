from django.contrib import admin

from .models import Batch, Enrollment, Session


for model in [Batch, Enrollment, Session]:
    admin.site.register(model)
