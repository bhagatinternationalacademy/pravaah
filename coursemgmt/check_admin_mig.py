from django.db import connection
cur = connection.cursor()
cur.execute("SELECT app, name FROM django_migrations WHERE app='admin'")
print(cur.fetchall())
