"""
django_accounting/ledger/models.py

General ledger: JournalEntry and JournalLine.
Decimal precision is read from accounting_settings at model definition time.
"""

from decimal import Decimal
from typing import Any, override

from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.db import models

from ..conf import accounting_settings
from ..mixins import BaseDocumentModel, BaseModel
from django_accounting.core.models import Account, FiscalPeriod

_DP = accounting_settings.MONEY_DECIMAL_PLACES


class JournalEntry(BaseDocumentModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        REVERSED = "reversed", "Reversed"
        VOIDED = "voided", "Voided"

    entry_number = models.CharField(max_length=30, unique=True)
    entry_date = models.DateField()
    description = models.CharField(max_length=500)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod,
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="journal_entries",
    )
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_journal_entries",
    )
    approved_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_journal_entries",
    )

    class Meta(BaseDocumentModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_journal_entry"
        ordering = ["-entry_date", "-created_at"]
        indexes = [
            models.Index(fields=["entry_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.entry_number} ({self.entry_date})"

    def is_balanced(self):
        totals = self.lines.aggregate(
            d=models.Sum("debit_amount"),
            c=models.Sum("credit_amount"),
        )
        return (totals["d"] or Decimal("0")) == (totals["c"] or Decimal("0"))
    
    @override
    def clean(self):
        if self.status == self.Status.POSTED and not self.is_balanced():
            raise ValidationError("A posted journal entry must be balanced.")
    
    @override
    def save(self, *args: Any, **kwargs: Any):
        from ..signals import journal_entry_posted
        prev_status = (
            JournalEntry.objects.filter(pk=self.pk).values_list("status", flat=True).first()
        )
        super().save(*args, **kwargs)
        if (
            prev_status != self.Status.POSTED
            and self.status == self.Status.POSTED
        ):
            journal_entry_posted.send(sender=self.__class__, journal_entry=self)


class JournalLine(BaseModel):
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines"
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="journal_lines"
    )
    debit_amount = models.DecimalField(
        max_digits=18, decimal_places=_DP, default=Decimal("0")
    )
    credit_amount = models.DecimalField(
        max_digits=18, decimal_places=_DP, default=Decimal("0")
    )
    memo = models.CharField(max_length=300, blank=True)
    line_number = models.PositiveIntegerField(default=1)

    class Meta(BaseModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_journal_line"
        ordering = ["line_number"]
        indexes = [models.Index(fields=["account"])]

    @override
    def __str__(self):
        return f"{self.journal_entry.entry_number} L{self.line_number}"
    
    @override
    def clean(self):
        debit = self.debit_amount or Decimal("0")
        credit = self.credit_amount or Decimal("0")
        if debit < 0 or credit < 0:
            raise ValidationError("Amounts must not be negative.")
        if debit > 0 and credit > 0:
            raise ValidationError("A line cannot have both debit and credit.")
        if debit == 0 and credit == 0:
            raise ValidationError("A line must have debit or credit.")
