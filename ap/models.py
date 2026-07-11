"""
django_accounting/ap/models.py
"""

from decimal import Decimal
from typing import override

from django.core.exceptions import ValidationError
from django.db import models

from ..conf import accounting_settings
from ..mixins import BaseActiveModel, BaseDocumentModel, BaseModel
from django_accounting.core.models import Account
from django_accounting.ledger.models import JournalEntry
from django_accounting.inventory.models import Item, ItemBatch
from django_accounting.tax.models import TaxGroup
from django_accounting.ar.models import Payment

_DP = accounting_settings.MONEY_DECIMAL_PLACES
_CDP = accounting_settings.COST_DECIMAL_PLACES
_QDP = accounting_settings.QTY_DECIMAL_PLACES


class Vendor(BaseActiveModel):
    name = models.CharField(max_length=300)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    payable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="ap_vendors"
    )
    payment_terms_days = models.PositiveIntegerField(
        default=accounting_settings.DEFAULT_PAYMENT_TERMS_DAYS
    )

    class Meta(BaseActiveModel.Meta):
        db_table = "accounting_vendor"
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active"])]
    
    @override
    def __str__(self):
        return self.name


class Bill(BaseDocumentModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        RECEIVED = "received", "Received"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        VOIDED = "voided", "Voided"

    bill_number = models.CharField(max_length=30)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="bills")
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.PROTECT, related_name="bill"
    )
    bill_date = models.DateField()
    due_date = models.DateField()
    vendor_reference = models.CharField(max_length=100, blank=True)
    subtotal = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    paid_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta(BaseDocumentModel.Meta):
        db_table = "accounting_bill"
        ordering = ["-bill_date"]
        unique_together = [("vendor", "bill_number")]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.bill_number} – {self.vendor.name}"

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount
    
    @override
    def clean(self):
        if self.bill_date and self.due_date and self.due_date < self.bill_date:
            raise ValidationError({"due_date": "Cannot be before bill_date."})

    @override
    def save(self, *args, **kwargs):
        from ..signals import bill_created, bill_paid, bill_voided
        is_new = self._state.adding
        prev_status = None
        if not is_new:
            prev_status = Bill.objects.filter(pk=self.pk).values_list("status", flat=True).first()
        super().save(*args, **kwargs)
        if is_new:
            bill_created.send(sender=self.__class__, bill=self)
        if prev_status != self.Status.PAID and self.status == self.Status.PAID:
            bill_paid.send(sender=self.__class__, bill=self)
        if prev_status != self.Status.VOIDED and self.status == self.Status.VOIDED:
            bill_voided.send(sender=self.__class__, bill=self)


class BillLine(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.PROTECT, related_name="bill_lines"
    )
    batch = models.ForeignKey(
        ItemBatch, null=True, blank=True, on_delete=models.PROTECT, related_name="bill_lines"
    )
    tax_group = models.ForeignKey(
        TaxGroup, null=True, blank=True, on_delete=models.PROTECT, related_name="bill_lines"
    )
    description = models.CharField(max_length=500, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=_QDP)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=_CDP)
    discount_pct = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0"))
    line_subtotal = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    line_number = models.PositiveIntegerField(default=1)

    class Meta(BaseModel.Meta):
        db_table = "accounting_bill_line"
        ordering = ["line_number"]
    
    @override
    def __str__(self):
        label = self.item.sku if self.item_id else self.description
        return f"{self.bill.bill_number} L{self.line_number} – {label}"

    @override
    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Must be greater than zero."})
        if self.item_id and self.item.requires_batch() and not self.batch_id:
            raise ValidationError({"batch": "Required for batch-tracked items."})


class BillPayment(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name="payment_allocations")
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="bill_allocations")
    applied_amount = models.DecimalField(max_digits=18, decimal_places=_DP)

    class Meta(BaseModel.Meta):
        db_table = "accounting_bill_payment"
        unique_together = [("bill", "payment")]
    
    @override
    def __str__(self):
        return f"{self.payment.payment_number} → {self.bill.bill_number} : {self.applied_amount}"

    @override
    def clean(self):
        if self.applied_amount is not None and self.applied_amount <= 0:
            raise ValidationError({"applied_amount": "Must be positive."})
        if self.payment_id and self.payment.payment_type != Payment.PaymentType.DISBURSEMENT:
            raise ValidationError({"payment": "Must be a disbursement-type payment."})

    @override
    def save(self, *args, **kwargs):
        from ..signals import disbursement_applied
        super().save(*args, **kwargs)
        disbursement_applied.send(
            sender=self.__class__,
            payment=self.payment, bill=self.bill, applied_amount=self.applied_amount,
        )
