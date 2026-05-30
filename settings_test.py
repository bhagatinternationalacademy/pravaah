import os
from .settings import *

# Override DATABASES to use SQLite for tests to avoid needing DB privileges
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
    }
}

# Speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Keep migrations as-is (we fake-applied them earlier), but ensure tests run isolated DB
