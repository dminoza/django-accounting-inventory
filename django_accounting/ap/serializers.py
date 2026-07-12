"""
django_accounting/ap/serializers.py
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from django_accounting.ap.models import Vendor, Bill, BillLine, BillPayment
from django_accounting.ar.models import Payment
from django_accounting.core.serializers import AccountNestedSerializer
from django_accounting.inventory.serializers import ItemNestedSerializer, ItemBatchNestedSerializer
from django_accounting.tax.serializers import TaxGroupNestedSerializer
from django_accounting.serializer_mixins import AccountingSerializerMixin


class VendorSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    payable_account_detail = AccountNestedSerializer(source="payable_account", read_only=True)
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            "id", "name", "email", "phone", "address", "tax_id",
            "payable_account", "payable_account_detail",
            "payment_terms_days", "outstanding_balance",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_outstanding_balance(self, obj):
        result = obj.bills.exclude(
            status__in=[Bill.Status.PAID, Bill.Status.VOIDED]
        ).aggregate(total=Sum("total_amount"), paid=Sum("paid_amount"))
        return (result["total"] or Decimal("0")) - (result["paid"] or Decimal("0"))


class VendorNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ["id", "name", "email"]
        read_only_fields = fields


class BillLineSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    item_detail = ItemNestedSerializer(source="item", read_only=True)
    batch_detail = ItemBatchNestedSerializer(source="batch", read_only=True)
    tax_group_detail = TaxGroupNestedSerializer(source="tax_group", read_only=True)

    class Meta:
        model = BillLine
        fields = [
            "id", "bill",
            "item", "item_detail", "batch", "batch_detail",
            "tax_group", "tax_group_detail",
            "description", "quantity", "unit_cost", "discount_pct",
            "line_subtotal", "tax_amount", "line_total", "line_number",
        ]
        read_only_fields = ["id", "bill", "line_subtotal", "tax_amount", "line_total"]

    def validate(self, data):
        quantity = data.get("quantity", getattr(self.instance, "quantity", None))
        item = data.get("item", getattr(self.instance, "item", None))
        batch = data.get("batch", getattr(self.instance, "batch", None))
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Must be greater than zero."})
        if item and item.requires_batch() and not batch:
            raise serializers.ValidationError({"batch": "Required for batch-tracked items."})
        return data


class BillLineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLine
        fields = [
            "item", "batch", "tax_group", "description",
            "quantity", "unit_cost", "discount_pct",
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


class BillSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    vendor_detail = VendorNestedSerializer(source="vendor", read_only=True)
    lines = BillLineSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        write_once_fields = ["bill_number", "vendor"]
        fields = [
            "id", "bill_number",
            "vendor", "vendor_detail",
            "journal_entry", "currency",
            "bill_date", "due_date", "vendor_reference",
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
        bill_date = data.get("bill_date", getattr(self.instance, "bill_date", None))
        due_date = data.get("due_date", getattr(self.instance, "due_date", None))
        if bill_date and due_date and due_date < bill_date:
            raise serializers.ValidationError({"due_date": "Cannot be before bill_date."})
        return data


class BillWriteSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    lines = BillLineWriteSerializer(many=True)

    class Meta:
        model = Bill
        write_once_fields = ["bill_number", "vendor"]
        fields = [
            "bill_number", "vendor",
            "bill_date", "due_date", "vendor_reference", "currency",
            "subtotal", "tax_amount", "total_amount",
            "status", "notes", "lines",
        ]

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("At least one line required.")
        return lines

    def validate(self, data):
        bill_date = data.get("bill_date", getattr(self.instance, "bill_date", None))
        due_date = data.get("due_date", getattr(self.instance, "due_date", None))
        if bill_date and due_date and due_date < bill_date:
            raise serializers.ValidationError({"due_date": "Cannot be before bill_date."})
        return data

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        bill = Bill.objects.create(**validated_data)
        BillLine.objects.bulk_create([BillLine(bill=bill, **l) for l in lines_data])
        return bill

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            BillLine.objects.bulk_create([BillLine(bill=instance, **l) for l in lines_data])
        return instance


class BillListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id", "bill_number", "vendor", "vendor_name",
            "bill_date", "due_date",
            "total_amount", "paid_amount", "balance_due", "status",
        ]
        read_only_fields = fields


class BillPaymentSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    bill_number = serializers.CharField(source="bill.bill_number", read_only=True)
    payment_number = serializers.CharField(source="payment.payment_number", read_only=True)

    class Meta:
        model = BillPayment
        fields = [
            "id", "bill", "bill_number",
            "payment", "payment_number",
            "applied_amount", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_applied_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Must be positive.")
        return value

    def validate(self, data):
        bill = data.get("bill", getattr(self.instance, "bill", None))
        payment = data.get("payment", getattr(self.instance, "payment", None))
        applied = data.get("applied_amount", getattr(self.instance, "applied_amount", Decimal("0")))

        if payment and payment.payment_type != Payment.PaymentType.DISBURSEMENT:
            raise serializers.ValidationError({"payment": "Must be a disbursement-type payment."})
        if bill and applied and applied > bill.balance_due:
            raise serializers.ValidationError(
                {"applied_amount": f"Exceeds bill balance due ({bill.balance_due})."}
            )
        if payment:
            already = payment.bill_allocations.exclude(
                pk=self.instance.pk if self.instance else None
            ).aggregate(t=Sum("applied_amount"))["t"] or Decimal("0")
            unapplied = payment.amount - already
            if applied and applied > unapplied:
                raise serializers.ValidationError(
                    {"applied_amount": f"Exceeds unapplied payment amount ({unapplied})."}
                )
        return data
