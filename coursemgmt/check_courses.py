from programs.models import Course
print('COUNT:', Course.objects.count())
for c in Course.objects.all()[:20]:
    print(c.course_id, c.course_code, c.course_name)
