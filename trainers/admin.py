from django.contrib import admin
from .models import Trainer

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('trainer_code', 'first_name', 'last_name', 'qualification', 'status', 'availability')
    search_fields = ('trainer_code', 'first_name', 'last_name', 'qualification')
