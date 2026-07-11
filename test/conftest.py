"""
tests/conftest.py

Pytest fixtures and Factory Boy factories for all accounting models.
"""

import pytest
import factory
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# ── Models ────────────────────────────────────────────────────────────────────
from django_accounting.core.models import Account, FiscalYear, FiscalPeriod
from django_accounting.ledger.models import JournalEntry, JournalLine
from django_accounting.tax.models import TaxAuthority, TaxRate, TaxGroup, TaxGroupRate
from django_accounting.inventory.models import (
    ItemCategory, Item, ItemBatch, Warehouse, WarehouseLocation, InventoryBalance,
)
from django_accounting.ar.models import Customer, Invoice, InvoiceLine, Payment, InvoicePayment
from django_accounting.ap.models import Vendor, Bill, BillLine, BillPayment


# ── API client fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(db):
    user = get_user_model().objects.create_user(username="tester", password="pass")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── Factories ─────────────────────────────────────────────────────────────────

class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account

    code = factory.Sequence(lambda n: f"1{n:04d}")
    name = factory.Sequence(lambda n: f"Account {n}")
    type = Account.AccountType.ASSET
    normal_balance = Account.NormalBalance.DEBIT
    is_active = True


class LiabilityAccountFactory(AccountFactory):
    code = factory.Sequence(lambda n: f"2{n:04d}")
    type = Account.AccountType.LIABILITY
    normal_balance = Account.NormalBalance.CREDIT


class RevenueAccountFactory(AccountFactory):
    code = factory.Sequence(lambda n: f"4{n:04d}")
    type = Account.AccountType.REVENUE
    normal_balance = Account.NormalBalance.CREDIT


class ExpenseAccountFactory(AccountFactory):
    code = factory.Sequence(lambda n: f"5{n:04d}")
    type = Account.AccountType.EXPENSE
    normal_balance = Account.NormalBalance.DEBIT


class FiscalYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FiscalYear

    year = factory.Sequence(lambda n: 2024 + n)
    start_date = factory.LazyAttribute(lambda o: f"{o.year}-01-01")
    end_date = factory.LazyAttribute(lambda o: f"{o.year}-12-31")
    is_closed = False


class FiscalPeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FiscalPeriod

    fiscal_year = factory.SubFactory(FiscalYearFactory)
    name = factory.Sequence(lambda n: f"Period {n}")
    start_date = "2025-01-01"
    end_date = "2025-01-31"
    is_closed = False


class TaxAuthorityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaxAuthority

    name = factory.Sequence(lambda n: f"Tax Authority {n}")
    code = factory.Sequence(lambda n: f"TA{n:03d}")
    jurisdiction = "Philippines"
    tax_payable_account = factory.SubFactory(LiabilityAccountFactory)
    tax_receivable_account = factory.SubFactory(AccountFactory)
    is_active = True


class TaxRateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaxRate

    tax_authority = factory.SubFactory(TaxAuthorityFactory)
    name = "VAT 12%"
    code = factory.Sequence(lambda n: f"VAT{n:03d}")
    rate_pct = Decimal("12.0000")
    tax_type = TaxRate.TaxType.VAT
    is_compound = False
    is_inclusive = False
    is_active = True


class TaxGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaxGroup

    name = factory.Sequence(lambda n: f"Tax Group {n}")
    code = factory.Sequence(lambda n: f"TG{n:03d}")
    is_active = True


class ItemCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemCategory

    name = factory.Sequence(lambda n: f"Category {n}")
    is_active = True


class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Item

    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")
    name = factory.Sequence(lambda n: f"Item {n}")
    category = factory.SubFactory(ItemCategoryFactory)
    item_type = Item.ItemType.PRODUCT
    unit_of_measure = Item.UnitOfMeasure.PIECE
    is_expirable = False
    is_batch_tracked = False
    is_active = True


class ExpirableItemFactory(ItemFactory):
    is_expirable = True
    is_batch_tracked = True


class ItemBatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemBatch

    item = factory.SubFactory(ItemFactory)
    batch_number = factory.Sequence(lambda n: f"BATCH-{n:05d}")
    lot_number = factory.Sequence(lambda n: f"LOT-{n:05d}")
    expiration_date = "2026-12-31"
    status = ItemBatch.Status.ACTIVE


class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    code = factory.Sequence(lambda n: f"WH{n:03d}")
    name = factory.Sequence(lambda n: f"Warehouse {n}")
    is_active = True


class WarehouseLocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WarehouseLocation

    warehouse = factory.SubFactory(WarehouseFactory)
    label = factory.Sequence(lambda n: f"A-{n:02d}-B")
    aisle = "A"
    rack = factory.Sequence(lambda n: f"{n:02d}")
    bin = "B"
    is_active = True


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    name = factory.Sequence(lambda n: f"Customer {n}")
    email = factory.Sequence(lambda n: f"customer{n}@example.com")
    receivable_account = factory.SubFactory(AccountFactory)
    payment_terms_days = 30
    is_active = True


class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vendor

    name = factory.Sequence(lambda n: f"Vendor {n}")
    email = factory.Sequence(lambda n: f"vendor{n}@example.com")
    payable_account = factory.SubFactory(LiabilityAccountFactory)
    payment_terms_days = 30
    is_active = True


class InvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invoice

    invoice_number = factory.Sequence(lambda n: f"INV-{n:05d}")
    customer = factory.SubFactory(CustomerFactory)
    invoice_date = "2025-01-15"
    due_date = "2025-02-15"
    subtotal = Decimal("1000.00")
    tax_amount = Decimal("120.00")
    total_amount = Decimal("1120.00")
    paid_amount = Decimal("0.00")
    status = Invoice.Status.DRAFT
    currency = "PHP"


class BillFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bill

    bill_number = factory.Sequence(lambda n: f"BILL-{n:05d}")
    vendor = factory.SubFactory(VendorFactory)
    bill_date = "2025-01-10"
    due_date = "2025-02-10"
    subtotal = Decimal("5000.00")
    tax_amount = Decimal("600.00")
    total_amount = Decimal("5600.00")
    paid_amount = Decimal("0.00")
    status = Bill.Status.DRAFT
    currency = "PHP"


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    payment_number = factory.Sequence(lambda n: f"PAY-{n:05d}")
    payment_type = Payment.PaymentType.RECEIPT
    customer = factory.SubFactory(CustomerFactory)
    payment_date = "2025-01-20"
    amount = Decimal("1120.00")
    method = Payment.PaymentMethod.BANK_TRANSFER


# ── Django fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def asset_account(db):
    return AccountFactory(code="1000", name="Cash")


@pytest.fixture
def liability_account(db):
    return LiabilityAccountFactory(code="2000", name="Accounts Payable")


@pytest.fixture
def revenue_account(db):
    return RevenueAccountFactory(code="4000", name="Sales Revenue")


@pytest.fixture
def expense_account(db):
    return ExpenseAccountFactory(code="5000", name="Cost of Goods Sold")


@pytest.fixture
def tax_authority(db, liability_account, asset_account):
    return TaxAuthorityFactory(
        tax_payable_account=liability_account,
        tax_receivable_account=asset_account,
    )


@pytest.fixture
def tax_rate(db, tax_authority):
    return TaxRateFactory(tax_authority=tax_authority)


@pytest.fixture
def tax_group(db, tax_rate):
    group = TaxGroupFactory()
    TaxGroupRate.objects.create(tax_group=group, tax_rate=tax_rate, apply_order=1)
    return group


@pytest.fixture
def fiscal_year(db):
    return FiscalYearFactory(year=2025)


@pytest.fixture
def fiscal_period(db, fiscal_year):
    return FiscalPeriodFactory(fiscal_year=fiscal_year)


@pytest.fixture
def warehouse(db):
    return WarehouseFactory(code="WH001", name="Main Warehouse")


@pytest.fixture
def warehouse_location(db, warehouse):
    return WarehouseLocationFactory(warehouse=warehouse, label="A-01-B")


@pytest.fixture
def item_category(db, asset_account, revenue_account, expense_account):
    return ItemCategoryFactory(
        inventory_account=asset_account,
        revenue_account=revenue_account,
        cogs_account=expense_account,
    )


@pytest.fixture
def item(db, item_category):
    return ItemFactory(category=item_category)


@pytest.fixture
def batch_item(db, item_category):
    return ExpirableItemFactory(category=item_category)


@pytest.fixture
def item_batch(db, batch_item):
    return ItemBatchFactory(item=batch_item, expiration_date="2026-12-31")


@pytest.fixture
def customer(db, asset_account):
    return CustomerFactory(receivable_account=asset_account)


@pytest.fixture
def vendor(db, liability_account):
    return VendorFactory(payable_account=liability_account)


@pytest.fixture
def invoice(db, customer):
    return InvoiceFactory(customer=customer)


@pytest.fixture
def bill(db, vendor):
    return BillFactory(vendor=vendor)


@pytest.fixture
def payment(db, customer):
    return PaymentFactory(customer=customer)
