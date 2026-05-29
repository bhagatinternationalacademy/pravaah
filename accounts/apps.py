from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pravaah.accounts'

    def ready(self):
        try:
            import pravaah.accounts.signals  # noqa: F401
        except Exception:
            pass
