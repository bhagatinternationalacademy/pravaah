from .settings import *

# Use the existing database for tests. WARNING: this will run tests against the
# configured DATABASES['default'] and may change or delete data.
TEST_RUNNER = 'pravaah.test_runner.NoDbTestRunner'

# If True, views will use an in-memory stub for the participants table during tests
# to avoid modifying or depending on external participant schemas.
FORCE_USE_STUB_PARTICIPANTS = True

# Ensure migrations run normally (we already fake-applied earlier)
