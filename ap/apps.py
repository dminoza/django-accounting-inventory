# django_accounting/ap/apps.py
from django.apps import AppConfig

class APConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting.ap"
    label = "accounting_ap"
    verbose_name = "Accounting – Accounts Payable"
