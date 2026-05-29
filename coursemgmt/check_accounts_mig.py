from django.db import connection
cur = connection.cursor()
cur.execute("SELECT app, name, applied FROM django_migrations WHERE app='accounts'")
print(cur.fetchall())
