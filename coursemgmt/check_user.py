from django.contrib.auth import get_user_model
from accounts.models import Role, UserRole
User = get_user_model()
print('users:', list(User.objects.filter(username='crudtester').values('id','username')))
print('roles:', list(Role.objects.all().values('role_id','role_name')))
print('user_roles:', list(UserRole.objects.filter(user__username='crudtester').values('user_role_id','user_id','role_id')))
