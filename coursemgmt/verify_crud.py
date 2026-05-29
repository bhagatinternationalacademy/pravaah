from django.test import Client
from programs.models import Course
c = Client()
assert c.login(username='crudtester', password='TestPass123')
course = Course.objects.get(course_name='Web Test Course 2')
print('found', course.course_id)
resp = c.post(f'/programs/courses/{course.course_id}/edit/', {'course_name':'Web Test Course 2 Updated','duration_hours':course.duration_hours,'fees':str(course.fees),'level':course.level,'status':course.status}, follow=True)
print('update status', resp.status_code, getattr(resp,'redirect_chain',None))
course.refresh_from_db()
print('new name', course.course_name)
# delete
resp2 = c.post(f'/programs/courses/{course.course_id}/delete/', follow=True)
print('delete status', resp2.status_code, getattr(resp2,'redirect_chain',None))
print('exists after delete', Course.objects.filter(pk=course.pk).exists())
