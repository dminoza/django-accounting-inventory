# django_accounting/ledger/apps.py
from django.apps import AppConfig

class LedgerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting.ledger"
    label = "accounting_ledger"
    verbose_name = "Accounting – Ledger"
