"""
Apps configuration for the Billing Management module.

Registers the billingmgmt app with Django and sets
the human-readable verbose name used in the admin interface.
"""

from django.apps import AppConfig


class BillingmgmtConfig(AppConfig):
    """Django application configuration for the Billing Management module."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billingmgmt'
    verbose_name = 'Billing Management'
