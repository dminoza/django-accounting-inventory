"""
django_accounting/ar/serializers.py
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from django_accounting.ar.models import Customer, Invoice, InvoiceLine, Payment, InvoicePayment
from django_accounting.core.serializers import AccountNestedSerializer
from django_accounting.inventory.serializers import ItemNestedSerializer, ItemBatchNestedSerializer
from django_accounting.tax.serializers import TaxGroupNestedSerializer
from ..serializer_mixins import AccountingSerializerMixin


class CustomerSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    receivable_account_detail = AccountNestedSerializer(source="receivable_account", read_only=True)
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id", "name", "email", "phone", "address", "tax_id",
            "receivable_account", "receivable_account_detail",
            "credit_limit", "payment_terms_days",
            "outstanding_balance", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_outstanding_balance(self, obj):
        result = obj.invoices.exclude(
            status__in=[Invoice.Status.PAID, Invoice.Status.VOIDED]
        ).aggregate(total=Sum("total_amount"), paid=Sum("paid_amount"))
        return (result["total"] or Decimal("0")) - (result["paid"] or Decimal("0"))


class CustomerNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email"]
        read_only_fields = fields


class InvoiceLineSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    item_detail = ItemNestedSerializer(source="item", read_only=True)
    batch_detail = ItemBatchNestedSerializer(source="batch", read_only=True)
    tax_group_detail = TaxGroupNestedSerializer(source="tax_group", read_only=True)

    class Meta:
        model = InvoiceLine
        fields = [
            "id", "invoice",
            "item", "item_detail", "batch", "batch_detail",
            "tax_group", "tax_group_detail",
            "description", "quantity", "unit_price", "discount_pct",
            "line_subtotal", "tax_amount", "line_total", "line_number",
        ]
        read_only_fields = ["id", "invoice", "line_subtotal", "tax_amount", "line_total"]

    def validate(self, data):
        quantity = data.get("quantity", getattr(self.instance, "quantity", None))
        item = data.get("item", getattr(self.instance, "item", None))
        batch = data.get("batch", getattr(self.instance, "batch", None))
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Must be greater than zero."})
        if item and item.requires_batch() and not batch:
            raise serializers.ValidationError({"batch": "Required for batch-tracked items."})
        return data


class InvoiceLineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = [
            "item", "batch", "tax_group", "description",
            "quantity", "unit_price", "discount_pct",
            "line_subtotal", "tax_amount", "line_total", "line_number",
        ]

    def validate(self, data):
        quantity = data.get("quantity")
        item = data.get("item")
        batch = data.get("batch")
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Must be greater than zero."})
        if item and item.requires_batch() and not batch:
            raise serializers.ValidationError({"batch": "Required for batch-tracked items."})
        return data


class InvoiceSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    customer_detail = CustomerNestedSerializer(source="customer", read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        write_once_fields = ["invoice_number", "customer"]
        fields = [
            "id", "invoice_number",
            "customer", "customer_detail",
            "journal_entry", "currency",
            "invoice_date", "due_date",
            "subtotal", "tax_amount", "total_amount", "paid_amount",
            "balance_due", "status", "notes",
            "lines", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "journal_entry",
            "subtotal", "tax_amount", "total_amount", "paid_amount",
            "balance_due", "created_at", "updated_at",
        ]

    def validate(self, data):
        inv_date = data.get("invoice_date", getattr(self.instance, "invoice_date", None))
        due_date = data.get("due_date", getattr(self.instance, "due_date", None))
        if inv_date and due_date and due_date < inv_date:
            raise serializers.ValidationError({"due_date": "Cannot be before invoice_date."})
        return data


class InvoiceWriteSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    lines = InvoiceLineWriteSerializer(many=True)

    class Meta:
        model = Invoice
        write_once_fields = ["invoice_number", "customer"]
        fields = [
            "invoice_number", "customer",
            "invoice_date", "due_date", "currency",
            "subtotal", "tax_amount", "total_amount",
            "status", "notes", "lines",
        ]

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("At least one line required.")
        return lines

    def validate(self, data):
        inv_date = data.get("invoice_date", getattr(self.instance, "invoice_date", None))
        due_date = data.get("due_date", getattr(self.instance, "due_date", None))
        if inv_date and due_date and due_date < inv_date:
            raise serializers.ValidationError({"due_date": "Cannot be before invoice_date."})
        return data

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        invoice = Invoice.objects.create(**validated_data)
        InvoiceLine.objects.bulk_create([InvoiceLine(invoice=invoice, **l) for l in lines_data])
        return invoice

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            InvoiceLine.objects.bulk_create(
                [InvoiceLine(invoice=instance, **l) for l in lines_data]
            )
        return instance


class InvoiceListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "customer", "customer_name",
            "invoice_date", "due_date",
            "total_amount", "paid_amount", "balance_due", "status",
        ]
        read_only_fields = fields


class PaymentSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    customer_detail = CustomerNestedSerializer(source="customer", read_only=True)
    unapplied_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        write_once_fields = ["payment_number", "payment_type"]
        fields = [
            "id", "payment_number", "payment_type",
            "customer", "customer_detail",
            "journal_entry", "payment_date", "amount", "method", "reference",
            "unapplied_amount", "notes", "created_at",
        ]
        read_only_fields = ["id", "journal_entry", "unapplied_amount", "created_at"]

    def get_unapplied_amount(self, obj):
        applied = obj.invoice_allocations.aggregate(t=Sum("applied_amount"))["t"] or Decimal("0")
        return obj.amount - applied

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Must be positive.")
        return value

    def validate(self, data):
        ptype = data.get("payment_type", getattr(self.instance, "payment_type", None))
        customer = data.get("customer", getattr(self.instance, "customer", None))
        if ptype == Payment.PaymentType.RECEIPT and not customer:
            raise serializers.ValidationError({"customer": "Required for receipt payments."})
        return data


class InvoicePaymentSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    payment_number = serializers.CharField(source="payment.payment_number", read_only=True)

    class Meta:
        model = InvoicePayment
        fields = [
            "id", "invoice", "invoice_number",
            "payment", "payment_number",
            "applied_amount", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_applied_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Must be positive.")
        return value

    def validate(self, data):
        invoice = data.get("invoice", getattr(self.instance, "invoice", None))
        payment = data.get("payment", getattr(self.instance, "payment", None))
        applied = data.get("applied_amount", getattr(self.instance, "applied_amount", Decimal("0")))

        if invoice and applied and applied > invoice.balance_due:
            raise serializers.ValidationError(
                {"applied_amount": f"Exceeds invoice balance due ({invoice.balance_due})."}
            )
        if payment:
            already = payment.invoice_allocations.exclude(
                pk=self.instance.pk if self.instance else None
            ).aggregate(t=Sum("applied_amount"))["t"] or Decimal("0")
            unapplied = payment.amount - already
            if applied and applied > unapplied:
                raise serializers.ValidationError(
                    {"applied_amount": f"Exceeds unapplied payment amount ({unapplied})."}
                )
        return data
