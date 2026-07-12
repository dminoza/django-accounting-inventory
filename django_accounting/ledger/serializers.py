"""
django_accounting/ledger/serializers.py
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from django_accounting.ledger.models import JournalEntry, JournalLine
from django_accounting.core.serializers import AccountNestedSerializer
from ..serializer_mixins import AccountingSerializerMixin


class JournalLineSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    account_detail = AccountNestedSerializer(source="account", read_only=True)

    class Meta:
        model = JournalLine
        fields = [
            "id", "journal_entry", "account", "account_detail",
            "debit_amount", "credit_amount", "memo", "line_number",
        ]
        read_only_fields = ["id", "journal_entry"]

    def validate(self, data):
        debit = data.get("debit_amount", Decimal("0")) or Decimal("0")
        credit = data.get("credit_amount", Decimal("0")) or Decimal("0")
        if debit < 0 or credit < 0:
            raise serializers.ValidationError("Amounts must not be negative.")
        if debit > 0 and credit > 0:
            raise serializers.ValidationError("Cannot have both debit and credit.")
        if debit == 0 and credit == 0:
            raise serializers.ValidationError("Must have debit or credit.")
        return data


class JournalLineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalLine
        fields = ["account", "debit_amount", "credit_amount", "memo", "line_number"]

    def validate(self, data):
        debit = data.get("debit_amount", Decimal("0")) or Decimal("0")
        credit = data.get("credit_amount", Decimal("0")) or Decimal("0")
        if debit < 0 or credit < 0:
            raise serializers.ValidationError("Amounts must not be negative.")
        if debit > 0 and credit > 0:
            raise serializers.ValidationError("Cannot have both debit and credit.")
        if debit == 0 and credit == 0:
            raise serializers.ValidationError("Must have debit or credit.")
        return data


class JournalEntrySerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)
    is_balanced = serializers.SerializerMethodField()
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = [
            "id", "entry_number", "entry_date", "description", "status",
            "fiscal_period", "currency",
            "reference_type", "reference_id",
            "created_by", "approved_by",
            "is_balanced", "total_debit", "total_credit",
            "lines", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def get_is_balanced(self, obj):
        return obj.is_balanced()

    def get_total_debit(self, obj):
        r = obj.lines.aggregate(t=Sum("debit_amount"))
        return r["t"] or Decimal("0")

    def get_total_credit(self, obj):
        r = obj.lines.aggregate(t=Sum("credit_amount"))
        return r["t"] or Decimal("0")


class JournalEntryWriteSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    """
    Accepts nested lines. Validates balance before saving.

    POST /journal-entries/
    {
        "entry_number": "JE-001",
        "entry_date": "2025-01-15",
        "description": "Cash sale",
        "lines": [
            {"account": "<uuid>", "debit_amount": "1000.00", "credit_amount": "0", "line_number": 1},
            {"account": "<uuid>", "debit_amount": "0", "credit_amount": "1000.00", "line_number": 2}
        ]
    }
    """
    lines = JournalLineWriteSerializer(many=True)

    class Meta:
        model = JournalEntry
        fields = [
            "entry_number", "entry_date", "description", "status",
            "fiscal_period", "currency", "reference_type", "reference_id", "lines",
        ]

    def validate_lines(self, lines):
        if len(lines) < 2:
            raise serializers.ValidationError("At least two lines required.")
        total_debit = sum(l.get("debit_amount", Decimal("0")) or Decimal("0") for l in lines)
        total_credit = sum(l.get("credit_amount", Decimal("0")) or Decimal("0") for l in lines)
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f"Not balanced: debits={total_debit}, credits={total_credit}."
            )
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        entry = JournalEntry.objects.create(**validated_data)
        JournalLine.objects.bulk_create(
            [JournalLine(journal_entry=entry, **l) for l in lines_data]
        )
        return entry

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            JournalLine.objects.bulk_create(
                [JournalLine(journal_entry=instance, **l) for l in lines_data]
            )
        return instance


class JournalEntryListSerializer(serializers.ModelSerializer):
    is_balanced = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = [
            "id", "entry_number", "entry_date", "description",
            "status", "fiscal_period", "is_balanced", "created_at",
        ]
        read_only_fields = fields

    def get_is_balanced(self, obj):
        return obj.is_balanced()
