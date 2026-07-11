# django-accounting

A configurable, installable double-entry accounting package for **Django REST Framework**.

Covers: Chart of Accounts · General Ledger · Accounts Receivable · Accounts Payable · Inventory with batch/expiry tracking · Multi-warehouse · Tax rates & groups.

---

## Installation

```bash
pip install django-accounting
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_accounting.core.apps.CoreConfig",
    "django_accounting.ledger.apps.LedgerConfig",
    "django_accounting.tax.apps.TaxConfig",
    "django_accounting.inventory.apps.InventoryConfig",
    "django_accounting.ar.apps.ARConfig",
    "django_accounting.ap.apps.APConfig",
]
```

Add URLs:

```python
# urls.py
path("api/accounting/", include("django_accounting.urls")),
```

Run migrations:

```bash
python manage.py makemigrations \
    accounting_core accounting_ledger accounting_tax \
    accounting_inventory accounting_ar accounting_ap
python manage.py migrate
```

---

## Configuration

All settings go under a single `ACCOUNTING` dict in `settings.py`.
Every key is optional — the defaults are shown below.

```python
ACCOUNTING = {
    # ── Currency & precision ─────────────────────────────────────────────
    "DEFAULT_CURRENCY": "PHP",       # ISO 4217 code
    "MONEY_DECIMAL_PLACES": 2,       # monetary amounts (invoice totals, etc.)
    "COST_DECIMAL_PLACES": 6,        # unit costs (preserves precision)
    "QTY_DECIMAL_PLACES": 4,         # quantities
    "RATE_DECIMAL_PLACES": 4,        # tax rates

    # ── Document number prefixes ─────────────────────────────────────────
    "INVOICE_NUMBER_PREFIX": "INV",
    "BILL_NUMBER_PREFIX": "BILL",
    "JOURNAL_ENTRY_PREFIX": "JE",
    "PAYMENT_NUMBER_PREFIX": "PAY",

    # ── Feature flags ────────────────────────────────────────────────────
    "ENABLE_BATCH_TRACKING": True,   # enforce batch FK on items/movements
    "ENABLE_EXPIRY_TRACKING": True,  # enforce expiration_date on batches
    "ENABLE_MULTI_WAREHOUSE": True,  # allow multiple warehouse locations
    "ENABLE_TAX": True,
    "ENABLE_SOFT_DELETE": False,     # soft-delete instead of hard-delete
    "AUTO_POST_JOURNAL_ENTRIES": False,

    # ── Defaults ─────────────────────────────────────────────────────────
    "DEFAULT_PAYMENT_TERMS_DAYS": 30,
    "DEFAULT_CREDIT_LIMIT": "0.00",
    "EXPIRY_WARNING_DAYS": 30,       # used by /item-batches/expiring_soon/

    # ── Swappable models ─────────────────────────────────────────────────
    "CUSTOMER_MODEL": None,          # e.g. "myapp.ExtendedCustomer"
    "VENDOR_MODEL": None,

    # ── Serializer behaviour ─────────────────────────────────────────────
    # Inject extra read-only fields onto any serializer by model name:
    "SERIALIZER_EXTRA_FIELDS": {
        "Invoice": ["erp_reference"],
        "Customer": ["loyalty_tier"],
    },

    # Mark fields as write-once (read-only on updates) by model name:
    "SERIALIZER_WRITE_ONCE_FIELDS": {
        "Invoice":      ["invoice_number", "customer"],
        "Bill":         ["bill_number", "vendor"],
        "JournalEntry": ["entry_number"],
    },
}
```

---

## API Endpoints

All endpoints are under `/api/accounting/` (or your configured prefix).

| Resource | URL |
|---|---|
| Accounts (COA) | `/accounts/` + `/accounts/tree/` |
| Fiscal Years | `/fiscal-years/` |
| Fiscal Periods | `/fiscal-periods/` |
| Journal Entries | `/journal-entries/` |
| Tax Authorities | `/tax-authorities/` |
| Tax Rates | `/tax-rates/` |
| Tax Groups | `/tax-groups/` |
| Item Categories | `/item-categories/` |
| Items | `/items/` |
| Item Batches | `/item-batches/` + `/item-batches/expiring_soon/` |
| Warehouses | `/warehouses/` |
| Warehouse Locations | `/warehouse-locations/` |
| Inventory Balances | `/inventory-balances/` (read-only) |
| Inventory Movements | `/inventory-movements/` |
| Customers | `/customers/` |
| Invoices | `/invoices/` |
| Payments | `/payments/` |
| Invoice Payments | `/invoice-payments/` |
| Vendors | `/vendors/` |
| Bills | `/bills/` |
| Bill Payments | `/bill-payments/` |

---

## Serializer features

### Dynamic field selection

Trim any response via query params — available on every endpoint:

```
GET /invoices/123/?fields=id,invoice_number,total_amount
GET /customers/456/?exclude=phone,address
```

Or pass via code:

```python
InvoiceSerializer(invoice, fields=["id", "total_amount"])
```

### Write-once fields

Fields listed in `ACCOUNTING["SERIALIZER_WRITE_ONCE_FIELDS"]` become
read-only on updates. The defaults protect `invoice_number`, `bill_number`,
and `entry_number`. Add your own:

```python
ACCOUNTING = {
    "SERIALIZER_WRITE_ONCE_FIELDS": {
        "Invoice": ["invoice_number", "customer", "currency"],
    }
}
```

### Extra fields

Inject additional read-only fields onto any serializer without subclassing:

```python
ACCOUNTING = {
    "SERIALIZER_EXTRA_FIELDS": {
        "Customer": ["loyalty_points"],   # must exist on the model
    }
}
```

---

## Extending models

### Swappable Customer / Vendor

```python
# myapp/models.py
from django_accounting.ar.models import Customer

class ExtendedCustomer(Customer):
    loyalty_points = models.IntegerField(default=0)
    assigned_rep = models.ForeignKey("auth.User", null=True, on_delete=models.SET_NULL)
```

```python
# settings.py
ACCOUNTING = {"CUSTOMER_MODEL": "myapp.ExtendedCustomer"}
```

### Lifecycle signals

Connect to any of these in your `AppConfig.ready()`:

```python
from django_accounting.signals import invoice_posted, batch_expiring_soon

@receiver(invoice_posted)
def on_invoice_posted(sender, invoice, journal_entry, **kwargs):
    send_invoice_email(invoice)

@receiver(batch_expiring_soon)
def on_expiry_warning(sender, batch, days_remaining, **kwargs):
    notify_warehouse_manager(batch, days_remaining)
```

Available signals: `account_created`, `journal_entry_posted`,
`invoice_created/posted/paid/voided`, `bill_created/posted/paid/voided`,
`payment_received`, `payment_applied`, `disbursement_made/applied`,
`inventory_received/issued/transferred/adjusted`,
`batch_created`, `batch_expired`, `batch_expiring_soon`, `low_stock_alert`.

---

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

---

## Package structure

```
django_accounting/
├── conf.py              ← ACCOUNTING settings + helpers
├── mixins.py            ← Abstract model mixins (UUID, timestamps, soft-delete, currency)
├── serializer_mixins.py ← DynamicFields, WriteOnce, ExtraFields
├── signals.py           ← Lifecycle signals
├── admin.py             ← Django admin registrations
├── apps.py              ← AppConfig for each sub-app
├── urls.py              ← DRF router + ViewSets
├── core/                ← Account, FiscalYear, FiscalPeriod
├── ledger/              ← JournalEntry, JournalLine
├── tax/                 ← TaxAuthority, TaxRate, TaxGroup, TaxLine
├── inventory/           ← Item, ItemBatch, Warehouse, InventoryBalance, InventoryMovement
├── ar/                  ← Customer, Invoice, Payment, InvoicePayment
└── ap/                  ← Vendor, Bill, BillPayment
```

---

## License

MIT
