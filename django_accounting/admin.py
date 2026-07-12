"""
django_accounting/admin.py
"""

from django.contrib import admin

from django_accounting.core.models import Account, FiscalYear, FiscalPeriod
from django_accounting.ledger.models import JournalEntry, JournalLine
from django_accounting.tax.models import TaxAuthority, TaxRate, TaxGroup, TaxGroupRate, TaxLine
from django_accounting.inventory.models import (
    ItemCategory, Item, ItemBatch,
    Warehouse, WarehouseLocation,
    InventoryBalance, InventoryMovement,
)
from django_accounting.ar.models import Customer, Invoice, InvoiceLine, Payment, InvoicePayment
from django_accounting.ap.models import Vendor, Bill, BillLine, BillPayment


# ── Inlines ───────────────────────────────────────────────────────────────────

class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 1
    fields = ("line_number", "account", "debit_amount", "credit_amount", "memo")


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    fields = (
        "line_number", "item", "batch", "description",
        "quantity", "unit_price", "discount_pct",
        "line_subtotal", "tax_amount", "line_total", "tax_group",
    )
    readonly_fields = ("line_subtotal", "tax_amount", "line_total")


class BillLineInline(admin.TabularInline):
    model = BillLine
    extra = 1
    fields = (
        "line_number", "item", "batch", "description",
        "quantity", "unit_cost", "discount_pct",
        "line_subtotal", "tax_amount", "line_total", "tax_group",
    )
    readonly_fields = ("line_subtotal", "tax_amount", "line_total")


class TaxGroupRateInline(admin.TabularInline):
    model = TaxGroupRate
    extra = 1
    fields = ("tax_rate", "apply_order")


class FiscalPeriodInline(admin.TabularInline):
    model = FiscalPeriod
    extra = 0
    fields = ("name", "start_date", "end_date", "is_closed")


# ── Core ──────────────────────────────────────────────────────────────────────

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "type", "normal_balance", "parent", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ("year", "start_date", "end_date", "is_closed")
    list_filter = ("is_closed",)
    inlines = [FiscalPeriodInline]


@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ("fiscal_year", "name", "start_date", "end_date", "is_closed")
    list_filter = ("fiscal_year", "is_closed")
    search_fields = ("name",)


# ── Ledger ────────────────────────────────────────────────────────────────────

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_number", "entry_date", "description", "status", "fiscal_period")
    list_filter = ("status",)
    search_fields = ("entry_number", "description")
    inlines = [JournalLineInline]
    readonly_fields = ("created_at", "updated_at")


# ── Tax ───────────────────────────────────────────────────────────────────────

@admin.register(TaxAuthority)
class TaxAuthorityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "jurisdiction", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = (
        "code", "name", "tax_authority", "rate_pct",
        "tax_type", "is_compound", "is_inclusive", "is_active",
    )
    list_filter = ("tax_type", "is_active", "is_compound")
    search_fields = ("code", "name")


@admin.register(TaxGroup)
class TaxGroupAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    inlines = [TaxGroupRateInline]


@admin.register(TaxLine)
class TaxLineAdmin(admin.ModelAdmin):
    list_display = ("source_type", "source_id", "tax_rate", "taxable_amount", "tax_amount")
    list_filter = ("source_type",)


# ── Inventory ─────────────────────────────────────────────────────────────────

@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "name", "category", "item_type",
        "unit_of_measure", "is_expirable", "is_batch_tracked", "is_active",
    )
    list_filter = ("item_type", "is_expirable", "is_batch_tracked", "is_active")
    search_fields = ("sku", "name")


@admin.register(ItemBatch)
class ItemBatchAdmin(admin.ModelAdmin):
    list_display = (
        "item", "batch_number", "lot_number",
        "manufacture_date", "expiration_date", "status",
    )
    list_filter = ("status",)
    search_fields = ("batch_number", "lot_number", "item__sku")
    date_hierarchy = "expiration_date"


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(WarehouseLocation)
class WarehouseLocationAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "label", "aisle", "rack", "bin", "is_active")
    list_filter = ("warehouse", "is_active")
    search_fields = ("label",)


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "item", "batch", "warehouse_location",
        "qty_on_hand", "qty_reserved", "unit_cost",
    )
    search_fields = ("item__sku", "batch__batch_number")


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_type", "item", "batch",
        "quantity", "unit_cost", "total_cost", "movement_date",
    )
    list_filter = ("movement_type",)
    search_fields = ("item__sku", "batch__batch_number")
    date_hierarchy = "movement_date"


# ── AR ────────────────────────────────────────────────────────────────────────

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "tax_id", "payment_terms_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "email", "tax_id")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number", "customer", "invoice_date",
        "due_date", "total_amount", "paid_amount", "status",
    )
    list_filter = ("status",)
    search_fields = ("invoice_number", "customer__name")
    date_hierarchy = "invoice_date"
    inlines = [InvoiceLineInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_number", "payment_type", "customer",
        "payment_date", "amount", "method",
    )
    list_filter = ("payment_type", "method")
    search_fields = ("payment_number", "customer__name")
    date_hierarchy = "payment_date"


# ── AP ────────────────────────────────────────────────────────────────────────

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "tax_id", "payment_terms_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "email", "tax_id")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "bill_number", "vendor", "bill_date",
        "due_date", "total_amount", "paid_amount", "status",
    )
    list_filter = ("status",)
    search_fields = ("bill_number", "vendor__name")
    date_hierarchy = "bill_date"
    inlines = [BillLineInline]
    readonly_fields = ("created_at", "updated_at")
