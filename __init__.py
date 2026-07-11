"""
django_accounting

A configurable double-entry accounting package for Django REST Framework.

Quick start
-----------
1. Add to INSTALLED_APPS:

    INSTALLED_APPS = [
        ...
        "django_accounting.core.apps.CoreConfig",
        "django_accounting.ledger.apps.LedgerConfig",
        "django_accounting.tax.apps.TaxConfig",
        "django_accounting.inventory.apps.InventoryConfig",
        "django_accounting.ar.apps.ARConfig",
        "django_accounting.ap.apps.APConfig",
    ]

2. Configure in settings.py (all optional — defaults shown):

    ACCOUNTING = {
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
        "CUSTOMER_MODEL": None,   # e.g. "myapp.Customer"
        "VENDOR_MODEL": None,
        "SERIALIZER_EXTRA_FIELDS": {},
        "SERIALIZER_WRITE_ONCE_FIELDS": {
            "Invoice": ["invoice_number", "customer"],
            "Bill": ["bill_number", "vendor"],
            "JournalEntry": ["entry_number"],
        },
    }

3. Add URLs:

    path("api/accounting/", include("django_accounting.urls")),

4. Run migrations:

    python manage.py makemigrations accounting_core accounting_ledger \\
        accounting_tax accounting_inventory accounting_ar accounting_ap
    python manage.py migrate
"""

default_app_config = "django_accounting.apps.CoreConfig"

__version__ = "1.0.0"
