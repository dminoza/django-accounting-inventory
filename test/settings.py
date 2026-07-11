"""
tests/settings.py — minimal Django settings for running the test suite.
"""

SECRET_KEY = "test-secret-key-not-for-production"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "django_accounting.core.apps.CoreConfig",
    "django_accounting.ledger.apps.LedgerConfig",
    "django_accounting.tax.apps.TaxConfig",
    "django_accounting.inventory.apps.InventoryConfig",
    "django_accounting.ar.apps.ARConfig",
    "django_accounting.ap.apps.APConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ROOT_URLCONF = "django_accounting.urls"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

# Package settings under test — override per test with @override_settings
ACCOUNTING = {
    "DEFAULT_CURRENCY": "PHP",
    "ENABLE_BATCH_TRACKING": True,
    "ENABLE_EXPIRY_TRACKING": True,
    "ENABLE_MULTI_WAREHOUSE": True,
}
