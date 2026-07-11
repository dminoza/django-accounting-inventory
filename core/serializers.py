"""
django_accounting/core/serializers.py
"""

from rest_framework import serializers

from django_accounting.core.models import Account, FiscalYear, FiscalPeriod
from django_accounting.serializer_mixins import AccountingSerializerMixin


class AccountSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    parent_code = serializers.CharField(source="parent.code", read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Account
        write_once_fields = ["code"]
        fields = [
            "id", "code", "name", "type", "normal_balance",
            "parent", "parent_code", "description",
            "is_active", "children_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_children_count(self, obj):
        return obj.children.count()

    def validate(self, data):
        instance = self.instance
        parent = data.get("parent", getattr(instance, "parent", None))
        acc_type = data.get("type", getattr(instance, "type", None))
        normal_balance = data.get("normal_balance", getattr(instance, "normal_balance", None))

        if instance and parent and parent.id == instance.id:
            raise serializers.ValidationError({"parent": "Cannot be own parent."})

        debit_types = {Account.AccountType.ASSET, Account.AccountType.EXPENSE}
        if acc_type and normal_balance:
            expected = (
                Account.NormalBalance.DEBIT
                if acc_type in debit_types
                else Account.NormalBalance.CREDIT
            )
            if normal_balance != expected:
                raise serializers.ValidationError(
                    {"normal_balance": f"Type '{acc_type}' requires '{expected}'."}
                )
        return data


class AccountNestedSerializer(serializers.ModelSerializer):
    """Minimal read-only embed used inside other serializers."""
    class Meta:
        model = Account
        fields = ["id", "code", "name", "type"]
        read_only_fields = fields


class AccountTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["id", "code", "name", "type", "normal_balance", "is_active", "children"]

    def get_children(self, obj):
        return AccountTreeSerializer(obj.children.filter(is_active=True), many=True).data


class FiscalPeriodSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = FiscalPeriod
        fields = ["id", "fiscal_year", "name", "start_date", "end_date", "is_closed"]
        read_only_fields = ["id"]

    def validate(self, data):
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        end = data.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and start >= end:
            raise serializers.ValidationError({"end_date": "Must be after start_date."})
        return data


class FiscalYearSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    periods = FiscalPeriodSerializer(many=True, read_only=True)
    period_count = serializers.IntegerField(source="periods.count", read_only=True)

    class Meta:
        model = FiscalYear
        fields = [
            "id", "year", "start_date", "end_date",
            "is_closed", "period_count", "periods", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        end = data.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and start >= end:
            raise serializers.ValidationError({"end_date": "Must be after start_date."})
        return data


class FiscalYearListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = ["id", "year", "start_date", "end_date", "is_closed"]
        read_only_fields = fields
