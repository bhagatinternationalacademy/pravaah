import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
import django
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT DATABASE(), USER()")
    print('DB_USER:', cur.fetchone())
    cur.execute("SELECT COUNT(*) FROM courses_tcm")
    print('COUNT:', cur.fetchone()[0])
    cur.execute("SELECT * FROM courses_tcm LIMIT 10")
    rows = cur.fetchall()
    print('ROWS:', len(rows))
    if rows:
        print([d[0] for d in cur.description])
        for r in rows:
            print(r)
    cur.execute("SHOW CREATE TABLE courses_tcm")
    print('SHOW CREATE TABLE (truncated):')
    print(cur.fetchone()[1][:1000])
