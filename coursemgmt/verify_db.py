from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
setup()
from programs.models import Course
print('COURSES_COUNT:', Course.objects.count())
print('LATEST_COURSES:')
for c in Course.objects.order_by('-course_id')[:20]:
    print(c.course_id, c.course_code or '', c.course_name)

check_names = ['Intro to TCM','Web Test Course','Web Test Course 2','Web Test Course 2 Updated','CRS-TXY537']
for n in check_names:
    qs = Course.objects.filter(course_name__icontains=n)
    print(f"FOUND '{n}':", qs.count(), 'ids:', list(qs.values_list('course_id', flat=True)))
