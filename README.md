# django-accounting

> A configurable, installable double-entry accounting package for **Django REST Framework**.
>
> Covers: Chart of Accounts · General Ledger · Accounts Receivable · Accounts Payable · Inventory with batch/expiry tracking · Multi-warehouse · Tax rates & groups · Lifecycle signals.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Quick Start](#2-quick-start)
3. [Configuration Reference](#3-configuration-reference)
4. [Package Structure](#4-package-structure)
5. [Models Reference](#5-models-reference)
   - [Core — Chart of Accounts & Fiscal](#51-core--chart-of-accounts--fiscal)
   - [Ledger — General Ledger](#52-ledger--general-ledger)
   - [Tax](#53-tax)
   - [Inventory](#54-inventory)
   - [Accounts Receivable](#55-accounts-receivable)
   - [Accounts Payable](#56-accounts-payable)
6. [Serializers Reference](#6-serializers-reference)
7. [API Endpoints Reference](#7-api-endpoints-reference)
8. [Signals Reference](#8-signals-reference)
9. [Model Mixins Reference](#9-model-mixins-reference)
10. [Serializer Mixins Reference](#10-serializer-mixins-reference)
11. [Extending the Package](#11-extending-the-package)
12. [Management Commands](#12-management-commands)
13. [Admin Registration](#13-admin-registration)
14. [Publishing to PyPI](#14-publishing-to-pypi)

---

## 1. Installation

```bash
pip install django-accounting
```

---

## 2. Quick Start

### Step 1 — Add to `INSTALLED_APPS`

**Single entry (recommended):**

```python
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",
    "django_accounting",
]
```

**Per sub-app (for fine-grained migration control):**

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "django_accounting.core.apps.CoreConfig",
    "django_accounting.ledger.apps.LedgerConfig",
    "django_accounting.tax.apps.TaxConfig",
    "django_accounting.inventory.apps.InventoryConfig",
    "django_accounting.ar.apps.ARConfig",
    "django_accounting.ap.apps.APConfig",
]
```

### Step 2 — Add URLs

```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    path("api/accounting/", include("django_accounting.urls")),
]
```

### Step 3 — Run migrations

```bash
# Single app
python manage.py makemigrations django_accounting
python manage.py migrate

# Per sub-app
python manage.py makemigrations \
    accounting_core accounting_ledger accounting_tax \
    accounting_inventory accounting_ar accounting_ap
python manage.py migrate
```

### Step 4 — Verify

Visit `http://localhost:8000/api/accounting/` in your browser. You should see the DRF browsable API root.

---

## 3. Configuration Reference

All settings live under a single `ACCOUNTING` dict in `settings.py`. Every key is optional — the defaults are shown below.

```python
# settings.py
ACCOUNTING = {

    # ── Currency & numeric precision ──────────────────────────────────────────
    # Controls decimal_places on all monetary, cost, quantity, and rate fields.
    # Changing these requires a new migration.
    "DEFAULT_CURRENCY":      "PHP",   # ISO 4217 — applied to all documents
    "MONEY_DECIMAL_PLACES":  2,       # invoice totals, payment amounts
    "COST_DECIMAL_PLACES":   6,       # unit costs — preserves COGS precision
    "QTY_DECIMAL_PLACES":    4,       # item quantities
    "RATE_DECIMAL_PLACES":   4,       # tax rate percentages

    # ── Document number prefixes ──────────────────────────────────────────────
    # Used when auto-generating document numbers in your service layer.
    "INVOICE_NUMBER_PREFIX":      "INV",    # e.g. INV-2025-000001
    "BILL_NUMBER_PREFIX":         "BILL",   # e.g. BILL-2025-000001
    "JOURNAL_ENTRY_PREFIX":       "JE",     # e.g. JE-2025-000001
    "PAYMENT_NUMBER_PREFIX":      "PAY",    # e.g. PAY-2025-000001

    # ── Feature flags ─────────────────────────────────────────────────────────
    # These gate validation at both model.clean() and serializer.validate() level.
    "ENABLE_BATCH_TRACKING":      True,   # enforce batch FK on movements/lines
    "ENABLE_EXPIRY_TRACKING":     True,   # enforce expiration_date on batches
    "ENABLE_MULTI_WAREHOUSE":     True,   # allow multiple warehouse locations
    "ENABLE_TAX":                 True,   # enable tax groups on lines
    "ENABLE_SOFT_DELETE":         False,  # soft-delete instead of hard-delete
    "AUTO_POST_JOURNAL_ENTRIES":  False,  # auto-post JE on document creation

    # ── Defaults ──────────────────────────────────────────────────────────────
    "DEFAULT_PAYMENT_TERMS_DAYS": 30,       # applied to new Customer/Vendor
    "DEFAULT_CREDIT_LIMIT":       "0.00",   # applied to new Customer
    "EXPIRY_WARNING_DAYS":        30,       # threshold for batch_expiring_soon signal

    # ── Swappable models ──────────────────────────────────────────────────────
    # Replace the built-in Customer/Vendor with your own extended model.
    # Must be a string in "app_label.ModelName" format.
    "CUSTOMER_MODEL":  None,    # e.g. "his_patients.Patient"
    "VENDOR_MODEL":    None,    # e.g. "his_procurement.Supplier"

    # ── Serializer behaviour ──────────────────────────────────────────────────
    # Inject extra read-only fields onto serializers by model name.
    # The field must exist as an attribute on the model.
    "SERIALIZER_EXTRA_FIELDS": {
        "Invoice":  ["erp_reference"],
        "Customer": ["loyalty_tier"],
    },

    # Fields that become read-only after the record is created.
    # Applied automatically by WriteOnceMixin on every serializer.
    "SERIALIZER_WRITE_ONCE_FIELDS": {
        "Invoice":      ["invoice_number", "customer"],
        "Bill":         ["bill_number", "vendor"],
        "JournalEntry": ["entry_number"],
    },
}
```

### Reading settings in your own code

```python
from django_accounting.conf import accounting_settings

currency = accounting_settings.DEFAULT_CURRENCY        # "PHP"
warn_days = accounting_settings.EXPIRY_WARNING_DAYS    # 30
```

### Swappable model helpers

```python
from django_accounting.conf import get_customer_model, get_vendor_model

Customer = get_customer_model()   # returns your custom model or the built-in
Vendor   = get_vendor_model()
```

---

## 4. Package Structure

```
django_accounting/
├── __init__.py             version + default_app_config
├── apps.py                 DjangoAccountingConfig (single AppConfig)
├── conf.py                 ACCOUNTING settings object + swappable model helpers
├── mixins.py               Abstract model mixins (UUID, timestamps, soft-delete, currency)
├── serializer_mixins.py    DynamicFields, WriteOnce, ExtraFields — on every serializer
├── signals.py              24 lifecycle signals
├── admin.py                Django admin registrations
├── urls.py                 DRF router + ViewSets
│
├── core/                   Chart of Accounts + Fiscal Calendar
│   ├── models.py           Account, FiscalYear, FiscalPeriod
│   ├── serializers.py
│   └── views.py
│
├── ledger/                 General Ledger
│   ├── models.py           JournalEntry, JournalLine
│   ├── serializers.py
│   └── views.py
│
├── tax/                    Tax Engine
│   ├── models.py           TaxAuthority, TaxRate, TaxGroup, TaxGroupRate, TaxLine
│   ├── serializers.py
│   └── views.py
│
├── inventory/              Inventory Management
│   ├── models.py           ItemCategory, Item, ItemBatch, Warehouse,
│   │                       WarehouseLocation, InventoryBalance, InventoryMovement
│   ├── serializers.py
│   └── views.py
│
├── ar/                     Accounts Receivable
│   ├── models.py           Customer, Invoice, InvoiceLine, Payment, InvoicePayment
│   ├── serializers.py
│   └── views.py
│
└── ap/                     Accounts Payable
    ├── models.py           Vendor, Bill, BillLine, BillPayment
    ├── serializers.py
    └── views.py
```

---

## 5. Models Reference

All models inherit from abstract base classes defined in `mixins.py`.

| Base Class | Fields added |
|---|---|
| `BaseModel` | `id` (UUID PK), `created_at`, `updated_at` |
| `BaseActiveModel` | + `is_active` |
| `BaseDocumentModel` | + `currency` |

---

### 5.1 Core — Chart of Accounts & Fiscal

#### `Account`

The chart of accounts. Supports hierarchical structure via self-referencing FK.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | Auto-generated |
| `code` | CharField(20) | Unique account code e.g. `1010` |
| `name` | CharField(200) | Account name |
| `type` | CharField | `asset` · `liability` · `equity` · `revenue` · `expense` |
| `normal_balance` | CharField | `debit` or `credit` |
| `parent` | FK(self) | Parent account for hierarchy |
| `description` | TextField | Optional notes |
| `is_active` | BooleanField | Default `True` |
| `created_at` | DateTimeField | Auto |
| `updated_at` | DateTimeField | Auto |

**Validation rules:**
- `normal_balance` must match `type`: `asset`/`expense` → `debit`; `liability`/`equity`/`revenue` → `credit`
- Account cannot be its own parent

**Signals fired:**
- `account_created` — on first save
- `account_deactivated` — when `is_active` flips to `False`

**Reverse relations:**
- `children` — child accounts (Manager)
- `journal_lines` — JournalLines posted to this account

---

#### `FiscalYear`

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `year` | PositiveIntegerField | Unique e.g. `2025` |
| `start_date` | DateField | |
| `end_date` | DateField | |
| `is_closed` | BooleanField | Closed years cannot accept new postings |
| `created_at` | DateTimeField | |

**Reverse relations:**
- `periods` — FiscalPeriod records

---

#### `FiscalPeriod`

Monthly (or custom) sub-period within a `FiscalYear`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `fiscal_year` | FK(FiscalYear) | |
| `name` | CharField(50) | e.g. `"January 2025"` |
| `start_date` | DateField | |
| `end_date` | DateField | |
| `is_closed` | BooleanField | Lock posting to this period |

**Reverse relations:**
- `journal_entries` — JournalEntries posted in this period

---

### 5.2 Ledger — General Ledger

#### `JournalEntry`

The header of every double-entry posting. Every financial event must produce a balanced `JournalEntry`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `entry_number` | CharField(30) | Unique e.g. `JE-2025-000001` |
| `entry_date` | DateField | |
| `description` | CharField(500) | |
| `status` | CharField | `draft` · `posted` · `reversed` · `voided` |
| `fiscal_period` | FK(FiscalPeriod) | Optional |
| `reference_type` | CharField(50) | `invoice` · `bill` · `payment` etc. |
| `reference_id` | UUIDField | UUID of the source document |
| `created_by` | FK(User) | |
| `approved_by` | FK(User) | |
| `currency` | CharField(3) | Defaults to `DEFAULT_CURRENCY` |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

**Methods:**
- `is_balanced() → bool` — returns `True` when sum of debits == sum of credits

**Signals fired:**
- `journal_entry_posted` — when `status` changes to `posted`

**Reverse relations:**
- `lines` — JournalLine records
- `inventory_movements` — InventoryMovements linked to this entry
- `invoice` — OneToOne reverse from Invoice
- `bill` — OneToOne reverse from Bill
- `payment` — OneToOne reverse from Payment

---

#### `JournalLine`

One debit or credit within a `JournalEntry`. Either `debit_amount` or `credit_amount` must be non-zero — never both.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `journal_entry` | FK(JournalEntry) | Cascades on delete |
| `account` | FK(Account) | GL account |
| `debit_amount` | DecimalField | 0 if this is a credit line |
| `credit_amount` | DecimalField | 0 if this is a debit line |
| `memo` | CharField(300) | Line-level description |
| `line_number` | PositiveIntegerField | Sort order |

**Validation rules:**
- Both amounts cannot be > 0 simultaneously
- Both amounts cannot be 0 simultaneously
- Neither amount can be negative

---

### 5.3 Tax

#### `TaxAuthority`

A government body that collects taxes (e.g. BIR, LGU).

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `name` | CharField(200) | e.g. `"Bureau of Internal Revenue"` |
| `code` | CharField(30) | Unique e.g. `"BIR"` |
| `jurisdiction` | CharField(200) | e.g. `"Philippines"` |
| `tax_payable_account` | FK(Account) | Liability account for output tax |
| `tax_receivable_account` | FK(Account) | Asset account for input tax |
| `is_active` | BooleanField | |

---

#### `TaxRate`

A single tax rate under a `TaxAuthority`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `tax_authority` | FK(TaxAuthority) | |
| `name` | CharField(200) | e.g. `"VAT 12%"` |
| `code` | CharField(30) | Unique e.g. `"VAT12"` |
| `rate_pct` | DecimalField | Percentage e.g. `12.0000` |
| `tax_type` | CharField | `vat` · `sales_tax` · `withholding` · `excise` · `other` |
| `is_compound` | BooleanField | Applied on top of accumulated tax |
| `is_inclusive` | BooleanField | Tax included in the line price |
| `is_active` | BooleanField | |
| `effective_from` | DateField | Optional start date |
| `effective_to` | DateField | Optional end date |

---

#### `TaxGroup`

A named bundle of one or more `TaxRate` records assigned to invoice/bill lines.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `name` | CharField(200) | e.g. `"Standard VAT"` |
| `code` | CharField(30) | Unique e.g. `"STVAT"` |
| `description` | TextField | |
| `is_active` | BooleanField | |

**Reverse relations:**
- `group_rates` — TaxGroupRate junction records

---

#### `TaxGroupRate`

Junction between `TaxGroup` and `TaxRate` with compound ordering.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `tax_group` | FK(TaxGroup) | |
| `tax_rate` | FK(TaxRate) | |
| `apply_order` | PositiveIntegerField | Lower = applied first |

---

#### `TaxLine`

Computed tax amount per rate per document line. Created when invoice/bill lines are processed.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `source_type` | CharField | `invoice_line` · `bill_line` |
| `source_id` | UUIDField | UUID of the InvoiceLine or BillLine |
| `tax_rate` | FK(TaxRate) | |
| `journal_line` | OneToOne(JournalLine) | GL posting for this tax amount |
| `taxable_amount` | DecimalField | Base amount tax was computed on |
| `tax_amount` | DecimalField | Computed tax |
| `is_inclusive` | BooleanField | Whether tax was included in price |

---

### 5.4 Inventory

#### `ItemCategory`

Hierarchical product taxonomy. Each category carries default GL accounts inherited by items.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `name` | CharField(200) | |
| `description` | TextField | |
| `parent` | FK(self) | Optional parent category |
| `inventory_account` | FK(Account) | Default asset account |
| `cogs_account` | FK(Account) | Default COGS expense account |
| `revenue_account` | FK(Account) | Default revenue account |
| `is_active` | BooleanField | |

---

#### `Item`

A stockable product or non-stock service. GL account resolution: item override → category → `None`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `sku` | CharField(100) | Unique stock-keeping unit |
| `name` | CharField(300) | |
| `description` | TextField | |
| `category` | FK(ItemCategory) | |
| `item_type` | CharField | `product` · `service` · `non_stock` |
| `unit_of_measure` | CharField | `pcs` · `box` · `kg` · `g` · `l` · `ml` · `m` · `pack` · `vial` · `tablet` · `capsule` · `other` |
| `reorder_point` | DecimalField | Triggers `low_stock_alert` when qty ≤ this |
| `reorder_qty` | DecimalField | Suggested replenishment quantity |
| `is_expirable` | BooleanField | Require `expiration_date` on batches |
| `is_batch_tracked` | BooleanField | Require batch FK on movements |
| `inventory_account` | FK(Account) | Item-level override |
| `cogs_account` | FK(Account) | Item-level override |
| `revenue_account` | FK(Account) | Item-level override |
| `is_active` | BooleanField | |

**Methods:**
- `requires_batch() → bool` — `True` when `is_batch_tracked AND ENABLE_BATCH_TRACKING`
- `requires_expiry() → bool` — `True` when `is_expirable AND ENABLE_EXPIRY_TRACKING`
- `get_inventory_account() → Account | None`
- `get_cogs_account() → Account | None`
- `get_revenue_account() → Account | None`

**Reverse relations:**
- `batches` — ItemBatch records
- `balances` — InventoryBalance records
- `movements` — InventoryMovement records
- `invoice_lines` — InvoiceLine records
- `bill_lines` — BillLine records

---

#### `ItemBatch`

A production batch / lot of an `Item` with optional expiration tracking.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `item` | FK(Item) | |
| `batch_number` | CharField(100) | Unique per item |
| `lot_number` | CharField(100) | |
| `manufacture_date` | DateField | |
| `expiration_date` | DateField | **Required** when `item.is_expirable=True` |
| `storage_conditions` | CharField(200) | e.g. `"Store at 2–8°C"` |
| `status` | CharField | `active` · `quarantine` · `expired` · `consumed` |
| `notes` | TextField | |

**Signals fired:**
- `batch_created` — on first save
- `batch_expiring_soon` — fired by `check_expiring_batches` management command
- `batch_expired` — fired by `check_expiring_batches` when `expiration_date < today`

---

#### `Warehouse`

A physical storage facility.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `code` | CharField(20) | Unique e.g. `"PHARM"` |
| `name` | CharField(200) | |
| `address` | TextField | |
| `is_active` | BooleanField | |

**Reverse relations:**
- `locations` — WarehouseLocation records

---

#### `WarehouseLocation`

A specific bin / rack / aisle within a `Warehouse`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `warehouse` | FK(Warehouse) | |
| `aisle` | CharField(20) | |
| `rack` | CharField(20) | |
| `bin` | CharField(20) | |
| `label` | CharField(50) | Human-readable e.g. `"A-01-B"` |
| `is_active` | BooleanField | |

---

#### `InventoryBalance`

Live on-hand quantity per `(item, batch, location)` triplet. Supports FEFO when ordered by `expiration_date ASC`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `item` | FK(Item) | |
| `batch` | FK(ItemBatch) | Null for non-batch-tracked items |
| `warehouse_location` | FK(WarehouseLocation) | |
| `qty_on_hand` | DecimalField | Current quantity |
| `qty_reserved` | DecimalField | Reserved for pending orders |
| `unit_cost` | DecimalField | Weighted average unit cost |
| `created_at` | DateTimeField | |

**Properties:**
- `qty_available` — `qty_on_hand - qty_reserved`

---

#### `InventoryMovement`

Immutable audit record of every stock movement. Use `select_for_update()` when creating to avoid race conditions.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `item` | FK(Item) | |
| `batch` | FK(ItemBatch) | Null for non-batch-tracked |
| `from_location` | FK(WarehouseLocation) | Source location |
| `to_location` | FK(WarehouseLocation) | Destination location |
| `journal_entry` | FK(JournalEntry) | GL posting for COGS |
| `movement_type` | CharField | `receipt` · `issue` · `transfer` · `adjustment` · `return_in` · `return_out` · `opening` |
| `quantity` | DecimalField | |
| `unit_cost` | DecimalField | |
| `total_cost` | DecimalField | `quantity × unit_cost` |
| `movement_date` | DateField | |
| `reference_type` | CharField(50) | `invoice` · `bill` · `prescription_line` etc. |
| `reference_id` | UUIDField | |
| `notes` | TextField | |

**Signals fired:**
- `inventory_received` — movement type `receipt`
- `inventory_issued` — movement type `issue`; also checks `low_stock_alert`
- `inventory_transferred` — movement type `transfer`
- `inventory_adjusted` — movement type `adjustment`

---

### 5.5 Accounts Receivable

#### `Customer`

A party that owes money. Extendable via `CUSTOMER_MODEL`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `name` | CharField(300) | |
| `email` | EmailField | |
| `phone` | CharField(50) | |
| `address` | TextField | |
| `tax_id` | CharField(50) | TIN or equivalent |
| `receivable_account` | FK(Account) | Trade receivables GL account |
| `credit_limit` | DecimalField | Default from `DEFAULT_CREDIT_LIMIT` |
| `payment_terms_days` | PositiveIntegerField | Default from `DEFAULT_PAYMENT_TERMS_DAYS` |
| `is_active` | BooleanField | |

**Reverse relations:**
- `invoices` — Invoice records
- `payments` — Payment records

---

#### `Invoice`

A sales invoice with nested lines.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `invoice_number` | CharField(30) | Unique, write-once |
| `customer` | FK(Customer) | Write-once |
| `journal_entry` | OneToOne(JournalEntry) | Auto-linked on posting |
| `invoice_date` | DateField | |
| `due_date` | DateField | Must be ≥ `invoice_date` |
| `subtotal` | DecimalField | Sum of line subtotals |
| `tax_amount` | DecimalField | Sum of line taxes |
| `total_amount` | DecimalField | `subtotal + tax_amount` |
| `paid_amount` | DecimalField | Sum of applied payments |
| `status` | CharField | `draft` · `sent` · `partially_paid` · `paid` · `overdue` · `voided` |
| `notes` | TextField | |
| `currency` | CharField(3) | |

**Properties:**
- `balance_due` — `total_amount - paid_amount`

**Signals fired:**
- `invoice_created` — on first save
- `invoice_paid` — when `status` → `paid`
- `invoice_voided` — when `status` → `voided`

**Reverse relations:**
- `lines` — InvoiceLine records
- `payment_allocations` — InvoicePayment records

---

#### `InvoiceLine`

One line on an `Invoice`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `invoice` | FK(Invoice) | Cascades on delete |
| `item` | FK(Item) | Optional |
| `batch` | FK(ItemBatch) | Required when `item.requires_batch()` |
| `tax_group` | FK(TaxGroup) | Optional |
| `description` | CharField(500) | |
| `quantity` | DecimalField | Must be > 0 |
| `unit_price` | DecimalField | |
| `discount_pct` | DecimalField | Percentage e.g. `10.0000` |
| `line_subtotal` | DecimalField | `qty × unit_price × (1 - discount/100)` |
| `tax_amount` | DecimalField | Computed from `tax_group` |
| `line_total` | DecimalField | `line_subtotal + tax_amount` |
| `line_number` | PositiveIntegerField | |

---

#### `Payment`

A customer receipt or vendor disbursement. Shared model for both AR and AP.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `payment_number` | CharField(30) | Unique |
| `payment_type` | CharField | `receipt` · `disbursement` |
| `customer` | FK(Customer) | Required for `receipt` payments |
| `journal_entry` | OneToOne(JournalEntry) | |
| `payment_date` | DateField | |
| `amount` | DecimalField | Must be > 0 |
| `method` | CharField | `cash` · `check` · `bank_transfer` · `credit_card` · `online` · `other` |
| `reference` | CharField(100) | Check number, transaction ID etc. |
| `notes` | TextField | |

**Signals fired:**
- `payment_received` — new `receipt` payment created
- `disbursement_made` — new `disbursement` payment created

**Reverse relations:**
- `invoice_allocations` — InvoicePayment records
- `bill_allocations` — BillPayment records

---

#### `InvoicePayment`

Junction — allocates part of a `Payment` to an `Invoice`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `invoice` | FK(Invoice) | |
| `payment` | FK(Payment) | |
| `applied_amount` | DecimalField | Must be > 0, cannot exceed `invoice.balance_due` |

**Signals fired:**
- `payment_applied` — on creation with kwargs `payment`, `invoice`, `applied_amount`

---

### 5.6 Accounts Payable

#### `Vendor`

A supplier that is owed money. Extendable via `VENDOR_MODEL`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `name` | CharField(300) | |
| `email` | EmailField | |
| `phone` | CharField(50) | |
| `address` | TextField | |
| `tax_id` | CharField(50) | |
| `payable_account` | FK(Account) | Trade payables GL account |
| `payment_terms_days` | PositiveIntegerField | |
| `is_active` | BooleanField | |

**Reverse relations:**
- `bills` — Bill records

---

#### `Bill`

A vendor bill (Purchase Order). Mirror of `Invoice`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `bill_number` | CharField(30) | Unique per vendor, write-once |
| `vendor` | FK(Vendor) | Write-once |
| `journal_entry` | OneToOne(JournalEntry) | |
| `bill_date` | DateField | |
| `due_date` | DateField | Must be ≥ `bill_date` |
| `vendor_reference` | CharField(100) | Vendor's own invoice number |
| `subtotal` | DecimalField | |
| `tax_amount` | DecimalField | |
| `total_amount` | DecimalField | |
| `paid_amount` | DecimalField | |
| `status` | CharField | `draft` · `received` · `partially_paid` · `paid` · `overdue` · `voided` |
| `notes` | TextField | |
| `currency` | CharField(3) | |

**Properties:**
- `balance_due` — `total_amount - paid_amount`

**Signals fired:**
- `bill_created` — on first save
- `bill_paid` — when `status` → `paid`
- `bill_voided` — when `status` → `voided`

**Reverse relations:**
- `lines` — BillLine records
- `payment_allocations` — BillPayment records

---

#### `BillLine`

One line on a `Bill`. Mirror of `InvoiceLine` but uses `unit_cost` instead of `unit_price`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `bill` | FK(Bill) | Cascades on delete |
| `item` | FK(Item) | Optional |
| `batch` | FK(ItemBatch) | Required when `item.requires_batch()` |
| `tax_group` | FK(TaxGroup) | Optional |
| `description` | CharField(500) | |
| `quantity` | DecimalField | Must be > 0 |
| `unit_cost` | DecimalField | |
| `discount_pct` | DecimalField | |
| `line_subtotal` | DecimalField | |
| `tax_amount` | DecimalField | |
| `line_total` | DecimalField | |
| `line_number` | PositiveIntegerField | |

---

#### `BillPayment`

Junction — allocates part of a disbursement `Payment` to a `Bill`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `bill` | FK(Bill) | |
| `payment` | FK(Payment) | Must be `payment_type=disbursement` |
| `applied_amount` | DecimalField | Must be > 0, cannot exceed `bill.balance_due` |

**Signals fired:**
- `disbursement_applied` — on creation with kwargs `payment`, `bill`, `applied_amount`

---

## 6. Serializers Reference

Every serializer in the package inherits `AccountingSerializerMixin` which bundles three behaviours — see [Section 10](#10-serializer-mixins-reference).

Most resources expose **three serializer variants**:

| Suffix | Used for | Notes |
|---|---|---|
| `*Serializer` | `GET` detail | Full read with nested `*_detail` fields |
| `*WriteSerializer` | `POST` / `PUT` / `PATCH` | Accepts nested children via `bulk_create` |
| `*ListSerializer` | `GET` list | Flat, no nesting, avoids N+1 |
| `*NestedSerializer` | Embedded inside other serializers | Minimal read-only |

### Key write serializers

**`JournalEntryWriteSerializer`**

Accepts nested `lines`. Validates `total_debit == total_credit` before saving.

```python
{
    "entry_number": "JE-2025-000001",
    "entry_date": "2025-01-15",
    "description": "Cash sale",
    "lines": [
        {"account": "<uuid>", "debit_amount": "1000.00", "credit_amount": "0.00", "line_number": 1},
        {"account": "<uuid>", "debit_amount": "0.00", "credit_amount": "1000.00", "line_number": 2}
    ]
}
```

**`InvoiceWriteSerializer`**

Accepts nested `lines`. At least one line required.

```python
{
    "invoice_number": "INV-2025-000001",
    "customer": "<uuid>",
    "invoice_date": "2025-01-15",
    "due_date": "2025-02-15",
    "lines": [
        {
            "description": "Consulting",
            "quantity": "1.0000",
            "unit_price": "5000.000000",
            "line_subtotal": "5000.00",
            "tax_amount": "0.00",
            "line_total": "5000.00",
            "line_number": 1
        }
    ]
}
```

**`TaxGroupWriteSerializer`**

Accepts nested `rates` with `apply_order` for compound stacking.

```python
{
    "name": "Standard VAT",
    "code": "STVAT",
    "rates": [
        {"tax_rate": "<vat12-uuid>", "apply_order": 1}
    ]
}
```

---

## 7. API Endpoints Reference

All endpoints sit under your configured prefix (default `/api/accounting/`).

### Core

| Method | URL | Description |
|---|---|---|
| `GET POST` | `/accounts/` | List / create accounts |
| `GET` | `/accounts/tree/` | Full COA as nested tree |
| `GET PUT PATCH DELETE` | `/accounts/<id>/` | Retrieve / update / delete |
| `GET POST` | `/fiscal-years/` | List / create |
| `GET PUT PATCH DELETE` | `/fiscal-years/<id>/` | Retrieve / update |
| `GET POST` | `/fiscal-periods/` | List / create |
| `GET PUT PATCH DELETE` | `/fiscal-periods/<id>/` | Retrieve / update |

### Ledger

| Method | URL | Description |
|---|---|---|
| `GET POST` | `/journal-entries/` | List / create |
| `GET PUT PATCH` | `/journal-entries/<id>/` | Retrieve / update |
| `GET POST` | `/journal-entries/<id>/lines/` | Nested lines |

### Tax

| Method | URL | Description |
|---|---|---|
| `GET POST` | `/tax-authorities/` | List / create |
| `GET PUT PATCH DELETE` | `/tax-authorities/<id>/` | Retrieve / update / delete |
| `GET POST` | `/tax-rates/` | List / create |
| `GET PUT PATCH DELETE` | `/tax-rates/<id>/` | Retrieve / update / delete |
| `GET POST` | `/tax-groups/` | List / create (with nested rates) |
| `GET PUT PATCH DELETE` | `/tax-groups/<id>/` | Retrieve / update / delete |

### Inventory

| Method | URL | Description |
|---|---|---|
| `GET POST` | `/item-categories/` | List / create |
| `GET PUT PATCH DELETE` | `/item-categories/<id>/` | |
| `GET POST` | `/items/` | List / create |
| `GET PUT PATCH DELETE` | `/items/<id>/` | |
| `GET POST` | `/item-batches/` | List / create |
| `GET` | `/item-batches/expiring_soon/` | Batches within `EXPIRY_WARNING_DAYS` |
| `GET PUT PATCH DELETE` | `/item-batches/<id>/` | |
| `GET POST` | `/warehouses/` | List / create |
| `GET PUT PATCH DELETE` | `/warehouses/<id>/` | |
| `GET POST` | `/warehouse-locations/` | List / create |
| `GET PUT PATCH DELETE` | `/warehouse-locations/<id>/` | |
| `GET` | `/inventory-balances/` | Read-only stock balances |
| `GET` | `/inventory-balances/<id>/` | |
| `GET POST` | `/inventory-movements/` | List / create movements |
| `GET` | `/inventory-movements/<id>/` | Retrieve (immutable) |

### Accounts Receivable

| Method | URL | Description |
|---|---|---|
| `GET POST` | `/customers/` | List / create |
| `GET PUT PATCH DELETE` | `/customers/<id>/` | |
| `GET POST` | `/invoices/` | List / create (with nested lines) |
| `GET PUT PATCH` | `/invoices/<id>/` | |
| `GET POST` | `/invoices/<id>/lines/` | Lines scoped to invoice |
| `GET PUT PATCH DELETE` | `/invoices/<id>/lines/<id>/` | |
| `GET POST` | `/payments/` | List / create |
| `GET PUT PATCH DELETE` | `/payments/<id>/` | |
| `GET POST` | `/invoice-payments/` | List / create allocations |
| `GET PUT PATCH DELETE` | `/invoice-payments/<id>/` | |

### Accounts Payable

| Method | URL | Description |
|---|---|---|
| `GET POST` | `/vendors/` | List / create |
| `GET PUT PATCH DELETE` | `/vendors/<id>/` | |
| `GET POST` | `/bills/` | List / create (with nested lines) |
| `GET PUT PATCH` | `/bills/<id>/` | |
| `GET POST` | `/bills/<id>/lines/` | Lines scoped to bill |
| `GET PUT PATCH DELETE` | `/bills/<id>/lines/<id>/` | |
| `GET POST` | `/bill-payments/` | List / create allocations |
| `GET PUT PATCH DELETE` | `/bill-payments/<id>/` | |

### Query parameters (all list endpoints)

| Parameter | Example | Description |
|---|---|---|
| `search` | `?search=amoxicillin` | Full-text search on `search_fields` |
| `ordering` | `?ordering=-invoice_date` | Field ordering, `-` for descending |
| `fields` | `?fields=id,code,name` | Return only specified fields |
| `exclude` | `?exclude=lines` | Exclude specified fields |
| `page` | `?page=2` | Pagination |
| Filter fields | `?status=paid` | Per-model filterset fields |

---

## 8. Signals Reference

Import path: `from django_accounting.signals import <signal_name>`

### Connection pattern

Always connect in `AppConfig.ready()`:

```python
# myapp/apps.py
class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self) -> None:
        import myapp.receivers  # noqa: F401
```

```python
# myapp/receivers.py
from django.dispatch import receiver
from django_accounting.signals import invoice_paid

@receiver(invoice_paid)
def on_invoice_paid(sender, invoice, **kwargs) -> None:
    send_receipt_sms(invoice.customer.phone, invoice)
```

### Signal table

| Signal | Fired when | Kwargs |
|---|---|---|
| `account_created` | New `Account` saved | `account` |
| `account_deactivated` | `Account.is_active` → `False` | `account` |
| `journal_entry_posted` | `JournalEntry.status` → `posted` | `journal_entry` |
| `journal_entry_reversed` | Reversal entry created | `original`, `reversal` |
| `invoice_created` | New `Invoice` saved | `invoice` |
| `invoice_posted` | Invoice linked to journal entry | `invoice`, `journal_entry` |
| `invoice_paid` | `Invoice.status` → `paid` | `invoice` |
| `invoice_voided` | `Invoice.status` → `voided` | `invoice` |
| `payment_received` | New receipt `Payment` created | `payment` |
| `payment_applied` | `InvoicePayment` saved | `payment`, `invoice`, `applied_amount` |
| `bill_created` | New `Bill` saved | `bill` |
| `bill_posted` | Bill linked to journal entry | `bill`, `journal_entry` |
| `bill_paid` | `Bill.status` → `paid` | `bill` |
| `bill_voided` | `Bill.status` → `voided` | `bill` |
| `disbursement_made` | New disbursement `Payment` created | `payment` |
| `disbursement_applied` | `BillPayment` saved | `payment`, `bill`, `applied_amount` |
| `inventory_received` | `InventoryMovement` type `receipt` | `movement`, `batch` |
| `inventory_issued` | `InventoryMovement` type `issue` | `movement`, `batch` |
| `inventory_transferred` | `InventoryMovement` type `transfer` | `movement` |
| `inventory_adjusted` | `InventoryMovement` type `adjustment` | `movement`, `reason` |
| `batch_created` | New `ItemBatch` saved | `batch` |
| `batch_expiring_soon` | `check_expiring_batches` command | `batch`, `days_remaining` |
| `batch_expired` | `check_expiring_batches` command | `batch` |
| `low_stock_alert` | qty ≤ `reorder_point` after issue/adjustment | `item`, `qty_on_hand`, `reorder_point` |

### Receiver examples

```python
# Invoice paid → SMS receipt
@receiver(invoice_paid)
def send_sms_receipt(sender, invoice, **kwargs) -> None:
    send_sms(invoice.customer.phone, f"Paid: {invoice.invoice_number}")

# Low stock → auto purchase request
@receiver(low_stock_alert)
def auto_purchase_request(sender, item, qty_on_hand, reorder_point, **kwargs) -> None:
    PurchaseRequest.objects.create(item=item, qty=item.reorder_qty)

# Batch expiring → email pharmacist
@receiver(batch_expiring_soon)
def warn_expiry(sender, batch, days_remaining, **kwargs) -> None:
    send_email(f"{batch.item.name} expires in {days_remaining} days")

# Payment applied → update AR aging
@receiver(payment_applied)
def refresh_aging(sender, payment, invoice, applied_amount, **kwargs) -> None:
    ARAgingReport.refresh_for_customer(invoice.customer_id)
```

---

## 9. Model Mixins Reference

Import path: `from django_accounting.mixins import <MixinName>`

| Mixin | Fields added | Notes |
|---|---|---|
| `UUIDPrimaryKeyMixin` | `id` (UUID PK, auto-generated) | |
| `TimestampMixin` | `created_at`, `updated_at` | Both `auto_now` |
| `ActiveMixin` | `is_active` (BooleanField, default True) | |
| `SoftDeleteMixin` | `is_deleted`, `deleted_at` | Gated by `ENABLE_SOFT_DELETE` |
| `CurrencyMixin` | `currency` (CharField(3)) | Defaults to `DEFAULT_CURRENCY` |
| `BaseModel` | `id`, `created_at`, `updated_at` | UUID + Timestamps |
| `BaseActiveModel` | + `is_active` | Most common base |
| `BaseDocumentModel` | + `currency` | For Invoice, Bill, JournalEntry |

### `SoftDeleteMixin` usage

```python
from django_accounting.mixins import SoftDeleteMixin, BaseModel

class MyModel(SoftDeleteMixin, BaseModel):
    name = models.CharField(max_length=100)

# Query
MyModel.objects.alive()         # excludes soft-deleted
MyModel.objects.with_deleted()  # includes soft-deleted
MyModel.all_objects.all()       # bypasses soft-delete manager

# Soft delete
obj.delete()      # sets is_deleted=True if ENABLE_SOFT_DELETE=True
obj.restore()     # clears is_deleted
obj.hard_delete() # permanent delete regardless of flag
```

### Composing mixins

```python
from django_accounting.mixins import (
    UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, CurrencyMixin
)
from django.db import models

# Build your own base
class MyBase(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, models.Model):
    class Meta:
        abstract = True
```

---

## 10. Serializer Mixins Reference

Import path: `from django_accounting.serializer_mixins import <MixinName>`

All three mixins are bundled into `AccountingSerializerMixin` which every package serializer inherits.

### `DynamicFieldsMixin`

Trim response fields via query param or constructor argument.

```python
# Via URL — any endpoint
GET /invoices/123/?fields=id,invoice_number,total_amount
GET /customers/456/?exclude=phone,address,email

# Via code
InvoiceSerializer(invoice, fields=["id", "total_amount"])
InvoiceSerializer(invoice, exclude=["lines"])
```

### `WriteOnceMixin`

Fields in `Meta.write_once_fields` or `ACCOUNTING["SERIALIZER_WRITE_ONCE_FIELDS"]` become read-only on updates.

```python
class InvoiceSerializer(serializers.ModelSerializer, AccountingSerializerMixin):
    class Meta:
        model = Invoice
        write_once_fields = ["invoice_number", "customer"]   # from Meta
        fields = [...]
```

Or via settings (no subclassing needed):

```python
ACCOUNTING = {
    "SERIALIZER_WRITE_ONCE_FIELDS": {
        "Invoice": ["invoice_number", "customer", "currency"],
    }
}
```

### `ExtraFieldsMixin`

Inject additional read-only model fields onto any serializer.

```python
ACCOUNTING = {
    "SERIALIZER_EXTRA_FIELDS": {
        "Customer": ["loyalty_points"],   # must exist on model
        "Invoice":  ["erp_reference"],
    }
}
```

### Using in your own serializers

```python
from django_accounting.serializer_mixins import AccountingSerializerMixin
from rest_framework import serializers

class MySerializer(serializers.ModelSerializer, AccountingSerializerMixin):
    class Meta:
        model = MyModel
        fields = [...]
        write_once_fields = ["code"]   # optional per-serializer override
```

---

## 11. Extending the Package

### Swappable Customer model

```python
# myapp/models.py
from django_accounting.ar.models import Customer

class Patient(Customer):
    patient_id = models.CharField(max_length=20, unique=True)
    philhealth_number = models.CharField(max_length=20, blank=True)

    class Meta(Customer.Meta):
        db_table = "his_patient"
```

```python
# settings.py
ACCOUNTING = {"CUSTOMER_MODEL": "myapp.Patient"}
```

```python
# myapp/migrations/0001_initial.py
class Migration(migrations.Migration):
    dependencies = [
        ("django_accounting", "0001_initial"),  # ← required
    ]
```

### Extending a serializer

```python
from django_accounting.ar.serializers import InvoiceSerializer
from django_accounting.ar.models import Invoice

class MyInvoiceSerializer(InvoiceSerializer):
    department = serializers.CharField(
        source="customer.department", read_only=True
    )

    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + ["department"]
```

### Extending a ViewSet

```python
from django_accounting.ar.views import InvoiceViewSet

class MyInvoiceViewSet(InvoiceViewSet):
    def get_queryset(self):
        # Filter to current user's company
        return super().get_queryset().filter(
            customer__company=self.request.user.company
        )
```

---

## 12. Management Commands

### `check_expiring_batches`

Fires `batch_expiring_soon` for batches within `EXPIRY_WARNING_DAYS` of expiry,
and `batch_expired` for batches already past their expiration date.

```bash
python manage.py check_expiring_batches
```

Schedule daily with cron:

```bash
# crontab -e
0 8 * * * /path/to/venv/bin/python manage.py check_expiring_batches
```

Or Celery Beat:

```python
# celery.py
app.conf.beat_schedule = {
    "check-expiring-batches": {
        "task": "myapp.tasks.run_expiry_check",
        "schedule": crontab(hour=8, minute=0),
    }
}
```

```python
# myapp/tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def run_expiry_check():
    call_command("check_expiring_batches")
```

---

## 13. Admin Registration

All models are registered in `django_accounting/admin.py`. Visit `/admin/` after adding `django.contrib.admin` to `INSTALLED_APPS`.

### Admin features

- **Account** — list with type/active filters, search by code/name
- **FiscalYear** — with nested FiscalPeriod inline
- **JournalEntry** — with JournalLine inline, balance status
- **TaxGroup** — with TaxGroupRate inline
- **Item** — batch/expiry flags, category filter
- **ItemBatch** — date hierarchy on `expiration_date`
- **Invoice** — with InvoiceLine inline, date hierarchy
- **Bill** — with BillLine inline, date hierarchy

---

## 14. Publishing to PyPI

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Test on TestPyPI first
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ django-accounting

# Publish to PyPI
twine upload dist/*
```

Store credentials in `~/.pypirc`:

```ini
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here
```

### Auto-publish with GitHub Actions

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build twine
      - run: python -m build
      - env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

---

## License

MIT — © 2025 Dario Minoza

---

## Changelog

### 1.0.3
- Initial release
- Double-entry general ledger with balanced journal entries
- Chart of accounts with self-referencing hierarchy
- Fiscal year and period management
- Tax authorities, rates, groups with compound stacking
- Inventory with batch/lot tracking, expiry dates, FEFO support
- Multi-warehouse stock balances
- Accounts Receivable — customers, invoices, payments
- Accounts Payable — vendors, bills, payments
- 24 lifecycle signals
- Configurable via `ACCOUNTING` settings dict
- Swappable Customer and Vendor models
- Dynamic field selection (`?fields=`, `?exclude=`)
- Write-once fields via settings
- Extra field injection via settings
- Soft-delete support
- Django admin registrations for all models
- DRF ViewSets + generic views + router
