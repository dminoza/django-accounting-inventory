from rest_framework import generics, filters

from .models import Customer, Invoice, InvoiceLine, Payment, InvoicePayment
from .serializers import (
    CustomerSerializer,
    InvoiceSerializer,
    InvoiceWriteSerializer,
    InvoiceListSerializer,
    InvoiceLineSerializer,
    PaymentSerializer,
    InvoicePaymentSerializer,
)


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.select_related("receivable_account").order_by("name")
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "email", "tax_id"]
    filterset_fields = ["is_active"]


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView[Customer]):
    queryset = Customer.objects.select_related("receivable_account")
    serializer_class = CustomerSerializer


class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = (
        Invoice.objects
        .select_related("customer", "journal_entry")
        .prefetch_related("lines__item", "lines__batch", "lines__tax_group")
        .order_by("-invoice_date")
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["invoice_number", "customer__name"]
    ordering_fields = ["invoice_date", "due_date", "total_amount"]
    filterset_fields = ["status", "customer", "invoice_date", "due_date"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InvoiceListSerializer
        return InvoiceWriteSerializer


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = (
        Invoice.objects
        .select_related("customer", "journal_entry")
        .prefetch_related("lines__item", "lines__batch", "lines__tax_group")
    )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return InvoiceWriteSerializer
        return InvoiceSerializer


class InvoiceLineListCreateView(generics.ListCreateAPIView):
    """Lines scoped to a specific invoice via URL."""
    serializer_class = InvoiceLineSerializer

    def get_queryset(self):
        return InvoiceLine.objects.filter(
            invoice_id=self.kwargs["invoice_id"]
        ).select_related("item", "batch", "tax_group")


class InvoiceLineDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvoiceLineSerializer

    def get_queryset(self):
        return InvoiceLine.objects.filter(
            invoice_id=self.kwargs["invoice_id"]
        ).select_related("item", "batch", "tax_group")


class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = (
        Payment.objects
        .select_related("customer", "journal_entry")
        .order_by("-payment_date")
    )
    serializer_class = PaymentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["payment_number", "customer__name"]
    filterset_fields = ["payment_type", "method", "customer"]


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.select_related("customer", "journal_entry")
    serializer_class = PaymentSerializer


class InvoicePaymentListCreateView(generics.ListCreateAPIView):
    queryset = InvoicePayment.objects.select_related(
        "invoice__customer", "payment"
    ).order_by("-created_at")
    serializer_class = InvoicePaymentSerializer
    filterset_fields = ["invoice", "payment"]


class InvoicePaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InvoicePayment.objects.select_related("invoice", "payment")
    serializer_class = InvoicePaymentSerializer
