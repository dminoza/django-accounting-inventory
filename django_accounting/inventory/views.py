# django_accounting/inventory/views.py

import datetime
from typing import ClassVar
from rest_framework import generics, filters
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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


class ItemCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ItemCategory.objects.select_related(
        "parent", "inventory_account", "cogs_account", "revenue_account"
    ).order_by("name")
    serializer_class = ItemCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["is_active", "parent"]


class ItemCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ItemCategory.objects.select_related(
        "parent", "inventory_account", "cogs_account", "revenue_account"
    )
    serializer_class = ItemCategorySerializer


class ItemListCreateView(generics.ListCreateAPIView):
    queryset = Item.objects.select_related(
        "category", "inventory_account", "cogs_account", "revenue_account"
    ).order_by("sku")
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["sku", "name"]
    ordering_fields = ["sku", "name"]
    filterset_fields = [
        "item_type", "is_active", "is_expirable", "is_batch_tracked", "category"
    ]


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Item.objects.select_related(
        "category", "inventory_account", "cogs_account", "revenue_account"
    )
    serializer_class = ItemSerializer


class ItemBatchListCreateView(generics.ListCreateAPIView):
    queryset = ItemBatch.objects.select_related("item").order_by("expiration_date")
    serializer_class = ItemBatchSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["batch_number", "lot_number", "item__sku"]
    filterset_fields = ["item", "status"]


class ItemBatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ItemBatch.objects.select_related("item")
    serializer_class = ItemBatchSerializer


class ItemBatchExpiringSoonView(generics.ListAPIView):
    """Returns batches expiring within EXPIRY_WARNING_DAYS days."""
    serializer_class = ItemBatchSerializer

    def get_queryset(self):
        from django.utils import timezone
        cutoff = timezone.now().date() + datetime.timedelta(
            days=accounting_settings.EXPIRY_WARNING_DAYS
        )
        return ItemBatch.objects.filter(
            expiration_date__lte=cutoff,
            expiration_date__gte=__import__("django.utils.timezone", fromlist=["now"]).now().date(),
            status=ItemBatch.Status.ACTIVE,
        ).select_related("item")


class WarehouseListCreateView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.prefetch_related("locations").order_by("code")
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]
    filterset_fields = ["is_active"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return WarehouseListSerializer
        return WarehouseSerializer


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Warehouse.objects.prefetch_related("locations")
    serializer_class = WarehouseSerializer


class WarehouseLocationListCreateView(generics.ListCreateAPIView):
    queryset = WarehouseLocation.objects.select_related("warehouse").order_by("label")
    serializer_class = WarehouseLocationSerializer
    filterset_fields = ["warehouse", "is_active"]
    search_fields = ["label"]


class WarehouseLocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WarehouseLocation.objects.select_related("warehouse")
    serializer_class = WarehouseLocationSerializer


class InventoryBalanceListView(generics.ListAPIView):
    """Read-only — updated only via InventoryMovement."""
    queryset = InventoryBalance.objects.select_related(
        "item", "batch", "warehouse_location__warehouse"
    ).order_by("item__sku")
    serializer_class = InventoryBalanceSerializer
    filterset_fields = ["item", "batch", "warehouse_location"]
    search_fields = ["item__sku", "batch__batch_number"]


class InventoryBalanceDetailView(generics.RetrieveAPIView):
    queryset = InventoryBalance.objects.select_related(
        "item", "batch", "warehouse_location__warehouse"
    )
    serializer_class = InventoryBalanceSerializer


class InventoryMovementListCreateView(generics.ListCreateAPIView):
    queryset = InventoryMovement.objects.select_related(
        "item", "batch", "from_location", "to_location"
    ).order_by("-movement_date")
    serializer_class = InventoryMovementSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["item__sku", "batch__batch_number"]
    filterset_fields = ["movement_type", "item", "batch", "movement_date"]


class InventoryMovementDetailView(generics.RetrieveAPIView):
    """Movements are immutable — retrieve only."""
    queryset = InventoryMovement.objects.select_related(
        "item", "batch", "from_location", "to_location"
    )
    serializer_class = InventoryMovementSerializer
