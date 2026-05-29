from django.contrib.auth import get_user_model
from accounts.models import Role, UserRole
User = get_user_model()

role, _ = Role.objects.get_or_create(role_name='Admin')
user, created = User.objects.get_or_create(username='crudtester', defaults={'email':'crudtester@example.com'})
if created:
    user.set_password('TestPass123')
    user.is_staff = True
    user.save()
# assign role
ur, _ = UserRole.objects.get_or_create(user=user, role=role)

from django.test import Client
c = Client()
logged = c.login(username='crudtester', password='TestPass123')
print('login:', logged)
resp = c.post('/programs/courses/create/', {'course_name':'Web Test Course','duration_hours':'12','fees':'100.00','level':'Beginner','status':'Active'}, follow=True)
print('status_code:', resp.status_code)
print('redirect_chain:', getattr(resp, 'redirect_chain', None))
from programs.models import Course
qs = Course.objects.filter(course_name='Web Test Course')
print('created_count:', qs.count())
if qs.exists():
    print('created id, code:', qs.first().course_id, qs.first().course_code)
