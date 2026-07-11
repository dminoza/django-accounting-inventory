# django_accounting/core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting.core"
    label = "accounting_core"
    verbose_name = "Accounting – Core"
