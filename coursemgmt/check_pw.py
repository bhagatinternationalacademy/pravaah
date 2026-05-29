from django.contrib.auth import get_user_model
User=get_user_model()
print('has_usable_password:', User.objects.get(username='crudtester').has_usable_password())
