# django_accounting/tax/apps.py
from django.apps import AppConfig

class TaxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting.tax"
    label = "accounting_tax"
    verbose_name = "Accounting – Tax"
