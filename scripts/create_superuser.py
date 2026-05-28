import os
import sys
# ensure project root is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pravaah.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

username = 'superadmin'
email = 'superadmin@gmail.com'
password = '1234'

if User.objects.filter(username=username).exists():
    print('Superuser already exists')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created:', username)
