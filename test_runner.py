from django.test.runner import DiscoverRunner

class NoDbTestRunner(DiscoverRunner):
    """Test runner that skips test database creation and teardown.

    WARNING: running tests with this runner will run tests against the live
    database configured in DATABASES. Tests that modify the DB will persist.
    Use only when you accept this risk.
    """
    def setup_databases(self, **kwargs):
        # Do not create or alter databases; return a dummy config expected by teardown
        return None

    def teardown_databases(self, old_config, **kwargs):
        # Nothing to tear down
        return
