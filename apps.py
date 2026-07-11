# django_accounting/apps.py
"""
Convenience re-export of all AppConfig classes.
Users can reference configs either from here or from each sub-app directly.
"""

from django_accounting.core.apps import CoreConfig
from django_accounting.ledger.apps import LedgerConfig
from django_accounting.tax.apps import TaxConfig
from django_accounting.inventory.apps import InventoryConfig
from django_accounting.ar.apps import ARConfig
from django_accounting.ap.apps import APConfig

__all__ = [
    "CoreConfig",
    "LedgerConfig",
    "TaxConfig",
    "InventoryConfig",
    "ARConfig",
    "APConfig",
]
