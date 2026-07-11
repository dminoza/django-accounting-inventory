"""
django_accounting/inventory/models.py

Items, batches, warehouses, balances, movements.
Feature flags from conf:
  ENABLE_BATCH_TRACKING  — enforce batch FK on movements/lines
  ENABLE_EXPIRY_TRACKING — enforce expiration_date on batches
  ENABLE_MULTI_WAREHOUSE — allow multiple warehouse locations
"""

from decimal import Decimal
from typing import override

from django.core.exceptions import ValidationError
from django.db import models

from ..conf import accounting_settings
from ..mixins import BaseActiveModel, BaseDocumentModel, BaseModel
from django_accounting.core.models import Account
from django_accounting.ledger.models import JournalEntry

_DP = accounting_settings.MONEY_DECIMAL_PLACES
_CDP = accounting_settings.COST_DECIMAL_PLACES
_QDP = accounting_settings.QTY_DECIMAL_PLACES


class ItemCategory(BaseActiveModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    inventory_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT,
        related_name="inventory_categories",
    )
    cogs_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT,
        related_name="cogs_categories",
    )
    revenue_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT,
        related_name="revenue_categories",
    )

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_item_category"
        verbose_name_plural = "item categories"
        ordering = ["name"]
    
    @override
    def __str__(self):
        return self.name
    
    @override
    def clean(self):
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError("A category cannot be its own parent.")


class Item(BaseActiveModel):
    class ItemType(models.TextChoices):
        PRODUCT = "product", "Product"
        SERVICE = "service", "Service"
        NON_STOCK = "non_stock", "Non-stock"

    class UnitOfMeasure(models.TextChoices):
        PIECE = "pcs", "Piece"
        BOX = "box", "Box"
        KILOGRAM = "kg", "Kilogram"
        GRAM = "g", "Gram"
        LITER = "l", "Liter"
        MILLILITER = "ml", "Milliliter"
        METER = "m", "Meter"
        PACK = "pack", "Pack"
        VIAL = "vial", "Vial"
        TABLET = "tablet", "Tablet"
        CAPSULE = "capsule", "Capsule"
        OTHER = "other", "Other"

    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        ItemCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    item_type = models.CharField(max_length=20, choices=ItemType.choices, default=ItemType.PRODUCT)
    unit_of_measure = models.CharField(
        max_length=20, choices=UnitOfMeasure.choices, default=UnitOfMeasure.PIECE
    )
    reorder_point = models.DecimalField(max_digits=14, decimal_places=_QDP, default=Decimal("0"))
    reorder_qty = models.DecimalField(max_digits=14, decimal_places=_QDP, default=Decimal("0"))

    # Per-item flag — also gated by conf flag globally
    is_expirable = models.BooleanField(default=False)
    is_batch_tracked = models.BooleanField(default=False)

    # GL overrides — falls back to category → system default
    inventory_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT, related_name="inventory_items"
    )
    cogs_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT, related_name="cogs_items"
    )
    revenue_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.PROTECT, related_name="revenue_items"
    )

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_item"
        ordering = ["sku"]
        indexes = [
            models.Index(fields=["item_type"]),
            models.Index(fields=["is_active"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.sku} – {self.name}"

    def get_inventory_account(self):
        return self.inventory_account or (self.category.inventory_account if self.category else None)

    def get_cogs_account(self):
        return self.cogs_account or (self.category.cogs_account if self.category else None)

    def get_revenue_account(self):
        return self.revenue_account or (self.category.revenue_account if self.category else None)

    def requires_batch(self):
        """True only when both item flag and global setting are enabled."""
        return self.is_batch_tracked and accounting_settings.ENABLE_BATCH_TRACKING

    def requires_expiry(self):
        return self.is_expirable and accounting_settings.ENABLE_EXPIRY_TRACKING


class ItemBatch(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        QUARANTINE = "quarantine", "Quarantine"
        EXPIRED = "expired", "Expired"
        CONSUMED = "consumed", "Fully Consumed"

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="batches")
    batch_number = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=100, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    storage_conditions = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        db_table = "accounting_item_batch"
        unique_together = [("item", "batch_number")]
        ordering = ["expiration_date", "batch_number"]
        indexes = [
            models.Index(fields=["expiration_date"]),
            models.Index(fields=["status"]),
        ]

    @override
    def __str__(self):
        exp = f" exp:{self.expiration_date}" if self.expiration_date else ""
        return f"{self.item.sku} / {self.batch_number}{exp}"
    
    @override
    def clean(self):
        if self.item_id and self.item.requires_expiry() and not self.expiration_date:
            raise ValidationError({"expiration_date": "Required for expirable items."})
        if (
            self.manufacture_date
            and self.expiration_date
            and self.manufacture_date > self.expiration_date
        ):
            raise ValidationError({"manufacture_date": "Cannot be after expiration_date."})
    
    @override
    def save(self, *args, **kwargs):
        from ..signals import batch_created
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            batch_created.send(sender=self.__class__, batch=self)


class Warehouse(BaseActiveModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_warehouse"
        ordering = ["code"]
    
    @override
    def __str__(self):
        return f"{self.code} – {self.name}"


class WarehouseLocation(BaseModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="locations")
    aisle = models.CharField(max_length=20, blank=True)
    rack = models.CharField(max_length=20, blank=True)
    bin = models.CharField(max_length=20, blank=True)
    label = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta(BaseModel.Meta):
        db_table = "accounting_warehouse_location"
        unique_together = [("warehouse", "label")]
        ordering = ["warehouse", "label"]
    
    @override
    def __str__(self):
        return f"{self.warehouse.code} / {self.label}"


class InventoryBalance(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="balances")
    batch = models.ForeignKey(
        ItemBatch, null=True, blank=True, on_delete=models.PROTECT, related_name="balances"
    )
    warehouse_location = models.ForeignKey(
        WarehouseLocation, on_delete=models.PROTECT, related_name="balances"
    )
    qty_on_hand = models.DecimalField(max_digits=14, decimal_places=_QDP, default=Decimal("0"))
    qty_reserved = models.DecimalField(max_digits=14, decimal_places=_QDP, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=_CDP, default=Decimal("0"))

    class Meta(BaseModel.Meta):
        db_table = "accounting_inventory_balance"
        unique_together = [("item", "batch", "warehouse_location")]
        indexes = [models.Index(fields=["item", "batch"])]
    
    @override
    def __str__(self):
        return f"{self.item.sku} @ {self.warehouse_location} = {self.qty_on_hand}"

    @property
    def qty_available(self):
        return self.qty_on_hand - self.qty_reserved


class InventoryMovement(BaseModel):
    class MovementType(models.TextChoices):
        RECEIPT = "receipt", "Purchase Receipt"
        ISSUE = "issue", "Issue / Sale"
        TRANSFER = "transfer", "Internal Transfer"
        ADJUSTMENT = "adjustment", "Stock Adjustment"
        RETURN_IN = "return_in", "Customer Return"
        RETURN_OUT = "return_out", "Vendor Return"
        OPENING = "opening", "Opening Balance"

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="movements")
    batch = models.ForeignKey(
        ItemBatch, null=True, blank=True, on_delete=models.PROTECT, related_name="movements"
    )
    from_location = models.ForeignKey(
        WarehouseLocation, null=True, blank=True,
        on_delete=models.PROTECT, related_name="outbound_movements",
    )
    to_location = models.ForeignKey(
        WarehouseLocation, null=True, blank=True,
        on_delete=models.PROTECT, related_name="inbound_movements",
    )
    journal_entry = models.ForeignKey(
        JournalEntry, null=True, blank=True,
        on_delete=models.PROTECT, related_name="inventory_movements",
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=_QDP)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=_CDP)
    total_cost = models.DecimalField(max_digits=18, decimal_places=_DP)
    movement_date = models.DateField()
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        db_table = "accounting_inventory_movement"
        ordering = ["-movement_date", "-created_at"]
        indexes = [
            models.Index(fields=["movement_type"]),
            models.Index(fields=["movement_date"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.movement_type} {self.item.sku} qty:{self.quantity}"
    
    @override
    def clean(self):
        if self.quantity == 0:
            raise ValidationError({"quantity": "Cannot be zero."})
        if self.movement_type == self.MovementType.TRANSFER:
            if not self.from_location or not self.to_location:
                raise ValidationError("Transfer requires both from_location and to_location.")
            if self.from_location_id == self.to_location_id:
                raise ValidationError({"to_location": "Must differ from from_location."})
        if self.item_id and self.item.requires_batch() and not self.batch_id:
            raise ValidationError({"batch": "Required for batch-tracked items."})
    
    @override
    def save(self, *args, **kwargs):
        from django_accounting.signals import (
            inventory_received, inventory_issued, inventory_transferred, inventory_adjusted
        )
        super().save(*args, **kwargs)
        sig_map = {
            self.MovementType.RECEIPT: inventory_received,
            self.MovementType.ISSUE: inventory_issued,
            self.MovementType.TRANSFER: inventory_transferred,
            self.MovementType.ADJUSTMENT: inventory_adjusted,
        }
        sig = sig_map.get(self.movement_type)
        if sig:
            sig.send(sender=self.__class__, movement=self, batch=self.batch)
