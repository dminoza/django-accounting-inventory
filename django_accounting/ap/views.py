from rest_framework import generics, filters

from .models import Vendor, Bill, BillLine, BillPayment
from .serializers import (
    VendorSerializer,
    BillSerializer,
    BillWriteSerializer,
    BillListSerializer,
    BillLineSerializer,
    BillPaymentSerializer,
)


class VendorListCreateView(generics.ListCreateAPIView):
    queryset = Vendor.objects.select_related("payable_account").order_by("name")
    serializer_class = VendorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "email", "tax_id"]
    filterset_fields = ["is_active"]


class VendorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.select_related("payable_account")
    serializer_class = VendorSerializer


class BillListCreateView(generics.ListCreateAPIView):
    queryset = (
        Bill.objects
        .select_related("vendor", "journal_entry")
        .prefetch_related("lines__item", "lines__batch", "lines__tax_group")
        .order_by("-bill_date")
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["bill_number", "vendor__name"]
    ordering_fields = ["bill_date", "due_date", "total_amount"]
    filterset_fields = ["status", "vendor", "bill_date", "due_date"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BillListSerializer
        return BillWriteSerializer


class BillDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = (
        Bill.objects
        .select_related("vendor", "journal_entry")
        .prefetch_related("lines__item", "lines__batch", "lines__tax_group")
    )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return BillWriteSerializer
        return BillSerializer


class BillLineListCreateView(generics.ListCreateAPIView):
    serializer_class = BillLineSerializer

    def get_queryset(self):
        return BillLine.objects.filter(
            bill_id=self.kwargs["bill_id"]
        ).select_related("item", "batch", "tax_group")


class BillLineDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BillLineSerializer

    def get_queryset(self):
        return BillLine.objects.filter(
            bill_id=self.kwargs["bill_id"]
        ).select_related("item", "batch", "tax_group")


class BillPaymentListCreateView(generics.ListCreateAPIView):
    queryset = BillPayment.objects.select_related(
        "bill__vendor", "payment"
    ).order_by("-created_at")
    serializer_class = BillPaymentSerializer
    filterset_fields = ["bill", "payment"]


class BillPaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BillPayment.objects.select_related("bill", "payment")
    serializer_class = BillPaymentSerializer
