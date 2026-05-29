from django.db import connection
cur = connection.cursor()
cur.execute("SELECT id, username, password FROM users WHERE username='crudtester'")
print(cur.fetchall())
