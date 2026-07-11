"""
django_accounting/serializer_mixins.py

Composable serializer mixins applied to every serializer in the package.

All behaviour is driven by ACCOUNTING settings so users can adjust it
without subclassing.
"""

from rest_framework import serializers


# ── Dynamic field selection ────────────────────────────────────────────────────

class DynamicFieldsMixin:
    """
    Trim serializer fields via a query-parameter or constructor argument.

    Via URL:
        GET /invoices/?fields=id,invoice_number,total_amount

    Via code:
        InvoiceSerializer(invoice, fields=["id", "total_amount"])
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", None)
        super().__init__(*args, **kwargs)

        # Query-param override
        request = self.context.get("request")
        if request:
            qp_fields = request.query_params.get("fields")
            qp_exclude = request.query_params.get("exclude")
            if qp_fields:
                fields = qp_fields.split(",")
            if qp_exclude:
                exclude = qp_exclude.split(",")

        if fields is not None:
            allowed = set(fields)
            for field in set(self.fields) - allowed:
                self.fields.pop(field)

        if exclude is not None:
            for field in exclude:
                self.fields.pop(field, None)


# ── Write-once fields ──────────────────────────────────────────────────────────

class WriteOnceMixin:
    """
    Fields declared in Meta.write_once_fields (or in ACCOUNTING settings)
    become read-only on updates.

    Meta takes precedence; ACCOUNTING['SERIALIZER_WRITE_ONCE_FIELDS'] is
    the package-level default the user can tweak without subclassing.

    class InvoiceSerializer(WriteOnceMixin, ...):
        class Meta:
            write_once_fields = ["invoice_number", "customer"]
    """

    def get_fields(self):
        fields = super().get_fields()
        if not self.instance:
            return fields  # create — all fields writable

        # 1. Meta-level declaration
        meta_once = list(getattr(self.Meta, "write_once_fields", []))

        # 2. Settings-level declaration
        from .conf import accounting_settings
        model_name = getattr(self.Meta, "model", None)
        if model_name:
            model_name = model_name.__name__
        settings_once = accounting_settings.SERIALIZER_WRITE_ONCE_FIELDS.get(
            model_name, []
        )

        for field_name in set(meta_once + settings_once):
            if field_name in fields:
                fields[field_name].read_only = True

        return fields


# ── Extra fields injected from settings ───────────────────────────────────────

class ExtraFieldsMixin:
    """
    Injects additional read-only fields declared in:

        ACCOUNTING = {
            "SERIALIZER_EXTRA_FIELDS": {
                "Invoice": ["erp_reference", "department_code"],
            }
        }

    The field must exist as an attribute on the model (or be a property).
    Non-existent fields are silently skipped.
    """

    def get_fields(self):
        fields = super().get_fields()
        from django_accounting.conf import accounting_settings

        model = getattr(self.Meta, "model", None)
        if not model:
            return fields

        extra = accounting_settings.SERIALIZER_EXTRA_FIELDS.get(
            model.__name__, []
        )
        for field_name in extra:
            if field_name not in fields and hasattr(model, field_name):
                fields[field_name] = serializers.ReadOnlyField()

        return fields


# ── Composite base every package serializer inherits ──────────────────────────

class AccountingSerializerMixin(DynamicFieldsMixin, WriteOnceMixin, ExtraFieldsMixin):
    """
    Single mixin that bundles all three behaviours.
    Apply to every serializer in the package so users get consistent
    field-trimming, write-once, and extra-field injection everywhere.
    """
    pass
