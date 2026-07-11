"""
django_accounting/inventory/views.py
"""

import datetime
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from ..conf import accounting_settings
from .models import (
    ItemCategory, Item, ItemBatch,
    Warehouse, WarehouseLocation,
    InventoryBalance, InventoryMovement,
)
from .serializers import (
    ItemCategorySerializer,
    ItemSerializer,
    ItemBatchSerializer,
    WarehouseSerializer,
    WarehouseListSerializer,
    WarehouseLocationSerializer,
    InventoryBalanceSerializer,
    InventoryMovementSerializer,
)


class ItemCategoryViewSet(viewsets.ModelViewSet[ItemCategory]):
    queryset = ItemCategory.objects.select_related(
        "parent", "inventory_account", "cogs_account", "revenue_account"
    ).order_by("name")
    serializer_class = ItemCategorySerializer
    filterset_fields = ["is_active", "parent"]
    search_fields = ["name"]


class ItemViewSet(viewsets.ModelViewSet[Item]):
    queryset = Item.objects.select_related(
        "category", "inventory_account", "cogs_account", "revenue_account"
    ).order_by("sku")
    serializer_class = ItemSerializer
    filterset_fields = ["item_type", "is_active", "is_expirable", "is_batch_tracked", "category"]
    search_fields = ["sku", "name"]


class ItemBatchViewSet(viewsets.ModelViewSet[ItemBatch]):
    queryset = ItemBatch.objects.select_related("item").order_by("expiration_date")
    serializer_class = ItemBatchSerializer
    filterset_fields = ["item", "status"]
    search_fields = ["batch_number", "lot_number", "item__sku"]

    @action(detail=False, methods=["get"])
    def expiring_soon(self, request: Request) -> Response:
        """Batches expiring within EXPIRY_WARNING_DAYS days."""
        from django.utils import timezone
        cutoff = timezone.now().date() + datetime.timedelta(
            days=accounting_settings.EXPIRY_WARNING_DAYS
        )
        qs = self.get_queryset().filter(
            expiration_date__lte=cutoff,
            expiration_date__gte=timezone.now().date(),
            status=ItemBatch.Status.ACTIVE,
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class WarehouseViewSet(viewsets.ModelViewSet[Warehouse]):
    queryset = Warehouse.objects.prefetch_related("locations").order_by("code")
    filterset_fields = ["is_active"]
    search_fields = ["code", "name"]

    def get_serializer_class(self):
        if self.action == "list":
            return WarehouseListSerializer
        return WarehouseSerializer


class WarehouseLocationViewSet(viewsets.ModelViewSet[WarehouseLocation]):
    queryset = WarehouseLocation.objects.select_related("warehouse").order_by("label")
    serializer_class = WarehouseLocationSerializer
    filterset_fields = ["warehouse", "is_active"]
    search_fields = ["label"]


class InventoryBalanceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only — balances are updated only via InventoryMovement."""
    queryset = InventoryBalance.objects.select_related(
        "item", "batch", "warehouse_location__warehouse"
    ).order_by("item__sku")
    serializer_class = InventoryBalanceSerializer
    filterset_fields = ["item", "batch", "warehouse_location"]
    search_fields = ["item__sku", "batch__batch_number"]


class InventoryMovementViewSet(viewsets.ModelViewSet[InventoryMovement]):
    queryset = InventoryMovement.objects.select_related(
        "item", "batch", "from_location", "to_location"
    ).order_by("-movement_date")
    serializer_class = InventoryMovementSerializer
    filterset_fields = ["movement_type", "item", "batch", "movement_date"]
    search_fields = ["item__sku", "batch__batch_number"]
