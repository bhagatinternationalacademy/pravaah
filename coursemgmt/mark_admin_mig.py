import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
import django
django.setup()
from django.db.migrations.recorder import MigrationRecorder
mr = MigrationRecorder.Migration
for name in ['0001_initial','0002_logentry_remove_auto_add','0003_logentry_add_action_flag_choices']:
    mr.objects.get_or_create(app='admin', name=name)
    print('marked', name)
