from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
setup()
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='crudtester')
user.set_password('TestPass123')
user.save()
print('password set')
