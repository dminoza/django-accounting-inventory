# django_accounting/apps.py
"""
Convenience re-export of all AppConfig classes.
Users can reference configs either from here or from each sub-app directly.
"""
from django.apps import AppConfig


class DjangoAccountingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting"
    label = "django_accounting"
    verbose_name = "Django Accounting"

    def ready(self) -> None:
        # Import all sub-app models so Django registers them
        import django_accounting.core.models       # noqa: F401
        import django_accounting.ledger.models     # noqa: F401
        import django_accounting.tax.models        # noqa: F401
        import django_accounting.inventory.models  # noqa: F401
        import django_accounting.ar.models         # noqa: F401
        import django_accounting.ap.models         # noqa: F401
