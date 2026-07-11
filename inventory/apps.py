# django_accounting/inventory/apps.py
from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_accounting.inventory"
    label = "accounting_inventory"
    verbose_name = "Accounting – Inventory"
