"""
django_accounting/ap/views.py
"""

from rest_framework import viewsets

from .models import Vendor, Bill, BillPayment
from .serializers import (
    VendorSerializer,
    BillSerializer,
    BillWriteSerializer,
    BillListSerializer,
    BillPaymentSerializer,
)


class VendorViewSet(viewsets.ModelViewSet[Vendor]):
    queryset = Vendor.objects.select_related("payable_account").order_by("name")
    serializer_class = VendorSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "email", "tax_id"]


class BillViewSet(viewsets.ModelViewSet[Bill]):
    queryset = (
        Bill.objects
        .select_related("vendor", "journal_entry")
        .prefetch_related("lines__item", "lines__batch", "lines__tax_group")
        .order_by("-bill_date")
    )
    filterset_fields = ["status", "vendor", "bill_date", "due_date"]
    search_fields = ["bill_number", "vendor__name", "vendor_reference"]

    def get_serializer_class(self):
        if self.action == "list":
            return BillListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BillWriteSerializer
        return BillSerializer


class BillPaymentViewSet(viewsets.ModelViewSet[BillPayment]):
    queryset = BillPayment.objects.select_related(
        "bill__vendor", "payment"
    ).order_by("-created_at")
    serializer_class = BillPaymentSerializer
    filterset_fields = ["bill", "payment"]
