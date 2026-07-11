"""
django_accounting/conf.py

Single source of truth for all package settings.
Override any key in your Django settings.py:

    ACCOUNTING = {
        "DEFAULT_CURRENCY": "USD",
        "CUSTOMER_MODEL": "myapp.Customer",
        "ENABLE_MULTI_WAREHOUSE": False,
    }
"""

from typing import Any, Mapping, TypeAlias

from django.conf import settings
from django.test.signals import setting_changed


DEFAULTS = {
    "DEFAULT_CURRENCY": "PHP",
    "MONEY_DECIMAL_PLACES": 2,
    "COST_DECIMAL_PLACES": 6,
    "QTY_DECIMAL_PLACES": 4,
    "RATE_DECIMAL_PLACES": 4,

    "INVOICE_NUMBER_PREFIX": "INV",
    "BILL_NUMBER_PREFIX": "BILL",
    "JOURNAL_ENTRY_PREFIX": "JE",
    "PAYMENT_NUMBER_PREFIX": "PAY",

    "ENABLE_BATCH_TRACKING": True,
    "ENABLE_EXPIRY_TRACKING": True,
    "ENABLE_MULTI_WAREHOUSE": True,
    "ENABLE_TAX": True,
    "ENABLE_SOFT_DELETE": False,
    "AUTO_POST_JOURNAL_ENTRIES": False,

    "DEFAULT_PAYMENT_TERMS_DAYS": 30,
    "DEFAULT_CREDIT_LIMIT": "0.00",
    "EXPIRY_WARNING_DAYS": 30,

    "CUSTOMER_MODEL": None,
    "VENDOR_MODEL": None,

    # Extra read-only fields injected per model name:
    # "SERIALIZER_EXTRA_FIELDS": {"Invoice": ["erp_ref", "dept_code"]}
    "SERIALIZER_EXTRA_FIELDS": {},

    # Fields that cannot be changed after creation, per model name:
    # "SERIALIZER_WRITE_ONCE_FIELDS": {"Invoice": ["invoice_number"]}
    "SERIALIZER_WRITE_ONCE_FIELDS": {
        "Invoice": ["invoice_number", "customer"],
        "Bill": ["bill_number", "vendor"],
        "JournalEntry": ["entry_number"],
    },
}

IMPORT_STRINGS = []

SettingValue: TypeAlias = (
    str | int | bool | float | list[object] | dict[str, object] | dict[str, str] | dict[str, list[str]] | None
)

class AccountingSettings:
    """
    Lazy settings wrapper.  Reads from settings.ACCOUNTING, falls back to DEFAULTS.
    Re-evaluated on every access so test overrides work without restarting.
    """

    def __init__(self, defaults: Mapping[str, SettingValue] | None) ->None:
        super().__init__()
        self._defaults = defaults or DEFAULTS
        self._cached = {}

    def _user_settings(self):
        return getattr(settings, "ACCOUNTING", {})

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._defaults:
            raise AttributeError(f"Invalid accounting setting: '{name}'")
        val = self._user_settings().get(name, self._defaults[name])
        return val

    def reload(self):
        self._cached = {}


accounting_settings = AccountingSettings(DEFAULTS)


def reload_accounting_settings(*args, **kwargs):
    setting = kwargs.get("setting")
    if setting == "ACCOUNTING":
        accounting_settings.reload()


setting_changed.connect(reload_accounting_settings)


# ── Swappable model helpers ────────────────────────────────────────────────────

def get_customer_model():
    model_str = accounting_settings.CUSTOMER_MODEL
    if model_str:
        from django.apps import apps
        return apps.get_model(model_str, require_ready=False)
    from django_accounting.ar.models import Customer
    return Customer


def get_vendor_model():
    model_str = accounting_settings.VENDOR_MODEL
    if model_str:
        from django.apps import apps
        return apps.get_model(model_str, require_ready=False)
    from django_accounting.ap.models import Vendor
    return Vendor
