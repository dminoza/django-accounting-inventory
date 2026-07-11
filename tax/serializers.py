"""
django_accounting/tax/serializers.py
"""

from rest_framework import serializers

from django_accounting.tax.models import TaxAuthority, TaxRate, TaxGroup, TaxGroupRate, TaxLine
from django_accounting.core.serializers import AccountNestedSerializer
from ..serializer_mixins import AccountingSerializerMixin


class TaxAuthoritySerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    tax_payable_account_detail = AccountNestedSerializer(source="tax_payable_account", read_only=True)
    tax_receivable_account_detail = AccountNestedSerializer(source="tax_receivable_account", read_only=True)

    class Meta:
        model = TaxAuthority
        fields = [
            "id", "name", "code", "jurisdiction",
            "tax_payable_account", "tax_payable_account_detail",
            "tax_receivable_account", "tax_receivable_account_detail",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TaxAuthorityNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxAuthority
        fields = ["id", "code", "name"]
        read_only_fields = fields


class TaxRateSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    tax_authority_detail = TaxAuthorityNestedSerializer(source="tax_authority", read_only=True)

    class Meta:
        model = TaxRate
        fields = [
            "id", "tax_authority", "tax_authority_detail",
            "name", "code", "rate_pct", "tax_type",
            "is_compound", "is_inclusive", "is_active",
            "effective_from", "effective_to", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_rate_pct(self, value):
        if value < 0:
            raise serializers.ValidationError("Cannot be negative.")
        return value

    def validate(self, data):
        eff_from = data.get("effective_from", getattr(self.instance, "effective_from", None))
        eff_to = data.get("effective_to", getattr(self.instance, "effective_to", None))
        if eff_from and eff_to and eff_from > eff_to:
            raise serializers.ValidationError({"effective_to": "Must be after effective_from."})
        return data


class TaxRateNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = ["id", "code", "name", "rate_pct", "tax_type", "is_compound", "is_inclusive"]
        read_only_fields = fields


class TaxGroupRateSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    tax_rate_detail = TaxRateNestedSerializer(source="tax_rate", read_only=True)

    class Meta:
        model = TaxGroupRate
        fields = ["id", "tax_group", "tax_rate", "tax_rate_detail", "apply_order"]
        read_only_fields = ["id", "tax_group"]


class TaxGroupRateWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxGroupRate
        fields = ["tax_rate", "apply_order"]


class TaxGroupSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    group_rates = TaxGroupRateSerializer(many=True, read_only=True)
    effective_rate_pct = serializers.SerializerMethodField()

    class Meta:
        model = TaxGroup
        fields = [
            "id", "name", "code", "description",
            "is_active", "group_rates", "effective_rate_pct", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_effective_rate_pct(self, obj):
        return sum(gr.tax_rate.rate_pct for gr in obj.group_rates.select_related("tax_rate"))


class TaxGroupWriteSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    rates = TaxGroupRateWriteSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = TaxGroup
        fields = ["name", "code", "description", "is_active", "rates"]

    def create(self, validated_data):
        rates_data = validated_data.pop("rates", [])
        group = TaxGroup.objects.create(**validated_data)
        TaxGroupRate.objects.bulk_create([TaxGroupRate(tax_group=group, **r) for r in rates_data])
        return group

    def update(self, instance, validated_data):
        rates_data = validated_data.pop("rates", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if rates_data is not None:
            instance.group_rates.all().delete()
            TaxGroupRate.objects.bulk_create(
                [TaxGroupRate(tax_group=instance, **r) for r in rates_data]
            )
        return instance


class TaxGroupNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxGroup
        fields = ["id", "code", "name"]
        read_only_fields = fields


class TaxLineSerializer(AccountingSerializerMixin, serializers.ModelSerializer):
    tax_rate_detail = TaxRateNestedSerializer(source="tax_rate", read_only=True)

    class Meta:
        model = TaxLine
        fields = [
            "id", "source_type", "source_id",
            "tax_rate", "tax_rate_detail",
            "journal_line", "taxable_amount", "tax_amount",
            "is_inclusive", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
