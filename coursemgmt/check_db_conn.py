import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
import django
django.setup()
from django.db import connection
import pprint
pprint.pprint(connection.settings_dict)
cur = connection.cursor()
cur.execute("SELECT DATABASE()")
print("current_db:", cur.fetchone()[0])
cur.execute("SELECT 1")
print("SELECT_1:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
print("tables_in_db:", cur.fetchone()[0])
