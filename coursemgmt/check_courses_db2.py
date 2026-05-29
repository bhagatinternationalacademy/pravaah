from programs.models import Course
from django.db import connection
print('HOST', connection.settings_dict.get('HOST'))
print('DB', connection.settings_dict.get('NAME'))
print('USER', connection.settings_dict.get('USER'))
cur = connection.cursor()
cur.execute('SELECT DATABASE(), USER()')
print('DATABASE,USER:', cur.fetchone())
print('COURSE COUNT:', Course.objects.count())
for c in Course.objects.order_by('-course_id')[:20]:
    print('ROW:', c.course_id, c.course_code, c.course_name)
try:
    cur.execute('SHOW CREATE TABLE courses_tcm')
    print('SHOW CREATE TABLE OK')
    print(cur.fetchone()[1][:1000])
except Exception as e:
    print('SHOW CREATE TABLE failed:', e)
