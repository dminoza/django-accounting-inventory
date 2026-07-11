# django_accounting/ar/apps.py
from django.apps import AppConfig

class ARConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting.ar"
    label = "accounting_ar"
    verbose_name = "Accounting – Accounts Receivable"
