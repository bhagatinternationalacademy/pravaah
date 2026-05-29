from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','training_management.settings')
setup()
from django.db import connection
cur = connection.cursor()
cur.execute("SELECT id, username, password FROM users WHERE username='crudtester'")
print(cur.fetchall())
