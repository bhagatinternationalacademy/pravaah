from .settings import *

# Use the existing database for tests. WARNING: this will run tests against the
# configured DATABASES['default'] and may change or delete data.
TEST_RUNNER = 'pravaah.test_runner.NoDbTestRunner'

# Ensure migrations run normally (we already fake-applied earlier)
