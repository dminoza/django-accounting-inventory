"""
django_accounting/tax/models.py
"""

from decimal import Decimal
from typing import override

from django.core.exceptions import ValidationError
from django.db import models

from ..conf import accounting_settings
from ..mixins import BaseActiveModel, BaseModel
from django_accounting.core.models import Account
from django_accounting.ledger.models import JournalLine

_DP = accounting_settings.MONEY_DECIMAL_PLACES
_RDP = accounting_settings.RATE_DECIMAL_PLACES


class TaxAuthority(BaseActiveModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    jurisdiction = models.CharField(max_length=200, blank=True)
    tax_payable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="tax_payable_authorities"
    )
    tax_receivable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="tax_receivable_authorities"
    )

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_tax_authority"
        verbose_name_plural = "tax authorities"
        ordering = ["name"]
    
    @override
    def __str__(self):
        return f"{self.code} – {self.name}"


class TaxRate(BaseActiveModel):
    class TaxType(models.TextChoices):
        VAT = "vat", "VAT / GST"
        SALES_TAX = "sales_tax", "Sales Tax"
        WITHHOLDING = "withholding", "Withholding Tax"
        EXCISE = "excise", "Excise Tax"
        OTHER = "other", "Other"

    tax_authority = models.ForeignKey(
        TaxAuthority, on_delete=models.PROTECT, related_name="rates"
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    rate_pct = models.DecimalField(max_digits=7, decimal_places=_RDP)
    tax_type = models.CharField(max_length=20, choices=TaxType.choices)
    is_compound = models.BooleanField(default=False)
    is_inclusive = models.BooleanField(default=False)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_tax_rate"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["effective_from", "effective_to"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.code} ({self.rate_pct}%)"
    
    @override
    def clean(self):
        if self.rate_pct is not None and self.rate_pct < 0:
            raise ValidationError({"rate_pct": "Cannot be negative."})
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValidationError({"effective_to": "Must be after effective_from."})


class TaxGroup(BaseActiveModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_tax_group"
        ordering = ["code"]
    
    @override
    def __str__(self):
        return f"{self.code} – {self.name}"


class TaxGroupRate(BaseModel):
    tax_group = models.ForeignKey(
        TaxGroup, on_delete=models.CASCADE, related_name="group_rates"
    )
    tax_rate = models.ForeignKey(
        TaxRate, on_delete=models.PROTECT, related_name="group_memberships"
    )
    apply_order = models.PositiveIntegerField(default=1)

    class Meta(BaseModel.Meta):
        db_table = "accounting_tax_group_rate"
        unique_together = [("tax_group", "tax_rate")]
        ordering = ["apply_order"]
    
    @override
    def __str__(self):
        return f"{self.tax_group.code} → {self.tax_rate.code}"


class TaxLine(BaseModel):
    class SourceType(models.TextChoices):
        INVOICE_LINE = "invoice_line", "Invoice Line"
        BILL_LINE = "bill_line", "Bill Line"

    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    source_id = models.UUIDField()
    tax_rate = models.ForeignKey(
        TaxRate, on_delete=models.PROTECT, related_name="tax_lines"
    )
    journal_line = models.OneToOneField(
        JournalLine,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="tax_line",
    )
    taxable_amount = models.DecimalField(max_digits=18, decimal_places=_DP)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=_DP)
    is_inclusive = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        db_table = "accounting_tax_line"
        indexes = [
            models.Index(fields=["source_type", "source_id"]),
            models.Index(fields=["tax_rate"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.source_type}:{self.source_id} – {self.tax_rate.code} {self.tax_amount}"
