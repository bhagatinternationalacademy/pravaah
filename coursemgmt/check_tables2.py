from django.db import connection
cur = connection.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()")
print([r[0] for r in cur.fetchall()])
