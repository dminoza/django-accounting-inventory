"""
django_accounting/ar/views.py
"""

from rest_framework import viewsets

from .models import Customer, Invoice, Payment, InvoicePayment
from .serializers import (
    CustomerSerializer,
    InvoiceSerializer,
    InvoiceWriteSerializer,
    InvoiceListSerializer,
    PaymentSerializer,
    InvoicePaymentSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet[Customer]):
    queryset = Customer.objects.select_related("receivable_account").order_by("name")
    serializer_class = CustomerSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "email", "tax_id"]


class InvoiceViewSet(viewsets.ModelViewSet[Invoice]):
    queryset = (
        Invoice.objects
        .select_related("customer", "journal_entry")
        .prefetch_related("lines__item", "lines__batch", "lines__tax_group")
        .order_by("-invoice_date")
    )
    filterset_fields = ["status", "customer", "invoice_date", "due_date"]
    search_fields = ["invoice_number", "customer__name"]

    def get_serializer_class(self):
        if self.action == "list":
            return InvoiceListSerializer
        if self.action in ("create", "update", "partial_update"):
            return InvoiceWriteSerializer
        return InvoiceSerializer


class PaymentViewSet(viewsets.ModelViewSet[Payment]):
    queryset = (
        Payment.objects
        .select_related("customer", "journal_entry")
        .order_by("-payment_date")
    )
    serializer_class = PaymentSerializer
    filterset_fields = ["payment_type", "method", "customer"]
    search_fields = ["payment_number", "reference", "customer__name"]


class InvoicePaymentViewSet(viewsets.ModelViewSet[InvoicePayment]):
    queryset = InvoicePayment.objects.select_related(
        "invoice__customer", "payment"
    ).order_by("-created_at")
    serializer_class = InvoicePaymentSerializer
    filterset_fields = ["invoice", "payment"]
