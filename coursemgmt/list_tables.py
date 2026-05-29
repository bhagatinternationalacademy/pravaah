from django.db import connection
cur = connection.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();")
tables = [r[0] for r in cur.fetchall()]
print('tables:', tables)
cur.execute("SELECT name, app FROM django_migrations ORDER BY applied" )
print('\n--- django_migrations (sample 50) ---')
for row in cur.fetchall()[:50]:
    print(row)
