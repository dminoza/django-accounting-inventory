"""
django_accounting/inventory/serializers.py
"""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from django_accounting.conf import accounting_settings
from django_accounting.inventory.models import (
    ItemCategory, Item, ItemBatch,
    Warehouse, WarehouseLocation,
    InventoryBalance, InventoryMovement,
)
from django_accounting.core.serializers import AccountNestedSerializer
from django_accounting.serializer_mixins import AccountingSerializerMixin


class ItemCategorySerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    inventory_account_detail = AccountNestedSerializer(source="inventory_account", read_only=True)
    cogs_account_detail = AccountNestedSerializer(source="cogs_account", read_only=True)
    revenue_account_detail = AccountNestedSerializer(source="revenue_account", read_only=True)

    class Meta:
        model = ItemCategory
        fields = [
            "id", "name", "description", "parent", "parent_name",
            "inventory_account", "inventory_account_detail",
            "cogs_account", "cogs_account_detail",
            "revenue_account", "revenue_account_detail",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        if self.instance:
            parent = data.get("parent", self.instance.parent)
            if parent and parent.id == self.instance.id:
                raise serializers.ValidationError({"parent": "Cannot be own parent."})
        return data


class ItemCategoryNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ["id", "name"]
        read_only_fields = fields


class ItemSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    category_detail = ItemCategoryNestedSerializer(source="category", read_only=True)
    inventory_account_detail = AccountNestedSerializer(source="inventory_account", read_only=True)
    cogs_account_detail = AccountNestedSerializer(source="cogs_account", read_only=True)
    revenue_account_detail = AccountNestedSerializer(source="revenue_account", read_only=True)
    qty_on_hand = serializers.SerializerMethodField()
    batch_tracking_enabled = serializers.SerializerMethodField()
    expiry_tracking_enabled = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id", "sku", "name", "description",
            "category", "category_detail",
            "item_type", "unit_of_measure",
            "reorder_point", "reorder_qty",
            "is_expirable", "is_batch_tracked",
            "batch_tracking_enabled", "expiry_tracking_enabled",
            "inventory_account", "inventory_account_detail",
            "cogs_account", "cogs_account_detail",
            "revenue_account", "revenue_account_detail",
            "qty_on_hand", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "qty_on_hand", "batch_tracking_enabled", "expiry_tracking_enabled",
        ]

    def get_qty_on_hand(self, obj):
        result = obj.balances.aggregate(total=Sum("qty_on_hand"))
        return result["total"] or Decimal("0")

    def get_batch_tracking_enabled(self, obj):
        return obj.requires_batch()

    def get_expiry_tracking_enabled(self, obj):
        return obj.requires_expiry()


class ItemNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "sku", "name", "unit_of_measure", "is_expirable", "is_batch_tracked"]
        read_only_fields = fields


class ItemBatchSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    item_detail = ItemNestedSerializer(source="item", read_only=True)
    qty_on_hand = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_to_expiry = serializers.SerializerMethodField()

    class Meta:
        model = ItemBatch
        fields = [
            "id", "item", "item_detail",
            "batch_number", "lot_number",
            "manufacture_date", "expiration_date",
            "storage_conditions", "status",
            "qty_on_hand", "is_expired", "days_to_expiry",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_qty_on_hand(self, obj):
        result = obj.balances.aggregate(total=Sum("qty_on_hand"))
        return result["total"] or Decimal("0")

    def get_is_expired(self, obj):
        if obj.expiration_date:
            return obj.expiration_date < timezone.now().date()
        return False

    def get_days_to_expiry(self, obj):
        if obj.expiration_date:
            delta = obj.expiration_date - timezone.now().date()
            return delta.days
        return None

    def validate(self, data):
        item = data.get("item", getattr(self.instance, "item", None))
        expiry = data.get("expiration_date", getattr(self.instance, "expiration_date", None))
        mfg = data.get("manufacture_date", getattr(self.instance, "manufacture_date", None))

        if item and item.requires_expiry() and not expiry:
            raise serializers.ValidationError(
                {"expiration_date": "Required for expirable items."}
            )
        if mfg and expiry and mfg > expiry:
            raise serializers.ValidationError(
                {"manufacture_date": "Cannot be after expiration_date."}
            )
        return data


class ItemBatchNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBatch
        fields = ["id", "batch_number", "lot_number", "expiration_date", "status"]
        read_only_fields = fields


class WarehouseLocationSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = WarehouseLocation
        fields = [
            "id", "warehouse", "warehouse_name",
            "aisle", "rack", "bin", "label", "is_active",
        ]
        read_only_fields = ["id"]


class WarehouseLocationNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseLocation
        fields = ["id", "label"]
        read_only_fields = fields


class WarehouseSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    locations = WarehouseLocationSerializer(many=True, read_only=True)
    location_count = serializers.IntegerField(source="locations.count", read_only=True)

    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "address", "is_active", "location_count", "locations", "created_at"]
        read_only_fields = ["id", "created_at"]


class WarehouseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "is_active"]
        read_only_fields = fields


class InventoryBalanceSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    item_detail = ItemNestedSerializer(source="item", read_only=True)
    batch_detail = ItemBatchNestedSerializer(source="batch", read_only=True)
    location_detail = WarehouseLocationNestedSerializer(source="warehouse_location", read_only=True)
    qty_available = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)

    class Meta:
        model = InventoryBalance
        fields = [
            "id", "item", "item_detail",
            "batch", "batch_detail",
            "warehouse_location", "location_detail",
            "qty_on_hand", "qty_reserved", "qty_available",
            "unit_cost", "created_at",
        ]
        read_only_fields = ["id", "qty_available", "created_at"]


class InventoryMovementSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    item_detail = ItemNestedSerializer(source="item", read_only=True)
    batch_detail = ItemBatchNestedSerializer(source="batch", read_only=True)
    from_location_detail = WarehouseLocationNestedSerializer(source="from_location", read_only=True)
    to_location_detail = WarehouseLocationNestedSerializer(source="to_location", read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            "id", "item", "item_detail",
            "batch", "batch_detail",
            "from_location", "from_location_detail",
            "to_location", "to_location_detail",
            "journal_entry", "movement_type",
            "quantity", "unit_cost", "total_cost",
            "movement_date", "reference_type", "reference_id",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at", "total_cost"]

    def validate(self, data):
        movement_type = data.get("movement_type", getattr(self.instance, "movement_type", None))
        from_loc = data.get("from_location", getattr(self.instance, "from_location", None))
        to_loc = data.get("to_location", getattr(self.instance, "to_location", None))
        quantity = data.get("quantity", getattr(self.instance, "quantity", None))
        item = data.get("item", getattr(self.instance, "item", None))
        batch = data.get("batch", getattr(self.instance, "batch", None))

        if quantity is not None and quantity == 0:
            raise serializers.ValidationError({"quantity": "Cannot be zero."})
        if movement_type == InventoryMovement.MovementType.TRANSFER:
            if not from_loc or not to_loc:
                raise serializers.ValidationError(
                    "Transfer requires both from_location and to_location."
                )
            if from_loc == to_loc:
                raise serializers.ValidationError(
                    {"to_location": "Must differ from from_location."}
                )
        if item and item.requires_batch() and not batch:
            raise serializers.ValidationError({"batch": "Required for batch-tracked items."})
        return data

    def create(self, validated_data):
        qty = validated_data.get("quantity")
        cost = validated_data.get("unit_cost")
        validated_data["total_cost"] = (qty * cost).quantize(Decimal("0.01"))
        return super().create(validated_data)
