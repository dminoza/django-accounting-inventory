"""
django_accounting/ar/models.py
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

_DP = accounting_settings.MONEY_DECIMAL_PLACES
_CDP = accounting_settings.COST_DECIMAL_PLACES
_QDP = accounting_settings.QTY_DECIMAL_PLACES


class Customer(BaseActiveModel):
    name = models.CharField(max_length=300)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    receivable_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="ar_customers"
    )
    credit_limit = models.DecimalField(
        max_digits=18, decimal_places=_DP,
        default=accounting_settings.DEFAULT_CREDIT_LIMIT,
    )
    payment_terms_days = models.PositiveIntegerField(
        default=accounting_settings.DEFAULT_PAYMENT_TERMS_DAYS
    )

    class Meta(BaseActiveModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_customer"
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active"])]
    
    @override
    def __str__(self):
        return self.name


class Invoice(BaseDocumentModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        VOIDED = "voided", "Voided"

    invoice_number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="invoices")
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice"
    )
    invoice_date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    paid_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta(BaseDocumentModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_invoice"
        ordering = ["-invoice_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["customer"]),
        ]

    @override
    def __str__(self):
        return f"{self.invoice_number} – {self.customer.name}"

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount
    
    @override
    def clean(self):
        if self.invoice_date and self.due_date and self.due_date < self.invoice_date:
            raise ValidationError({"due_date": "Cannot be before invoice_date."})

    @override
    def save(self, *args, **kwargs):
        from django_accounting.signals import invoice_created, invoice_paid, invoice_voided
        is_new = self._state.adding
        prev_status = None
        if not is_new:
            prev_status = Invoice.objects.filter(pk=self.pk).values_list("status", flat=True).first()
        super().save(*args, **kwargs)
        if is_new:
            invoice_created.send(sender=self.__class__, invoice=self)
        if prev_status != self.Status.PAID and self.status == self.Status.PAID:
            invoice_paid.send(sender=self.__class__, invoice=self)
        if prev_status != self.Status.VOIDED and self.status == self.Status.VOIDED:
            invoice_voided.send(sender=self.__class__, invoice=self)


class InvoiceLine(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice_lines"
    )
    batch = models.ForeignKey(
        ItemBatch, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice_lines"
    )
    tax_group = models.ForeignKey(
        TaxGroup, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice_lines"
    )
    description = models.CharField(max_length=500, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=_QDP)
    unit_price = models.DecimalField(max_digits=18, decimal_places=_CDP)
    discount_pct = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0"))
    line_subtotal = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=_DP, default=Decimal("0"))
    line_number = models.PositiveIntegerField(default=1)

    class Meta(BaseModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_invoice_line"
        ordering = ["line_number"]
    
    @override
    def __str__(self):
        label = self.item.sku if self.item_id else self.description
        return f"{self.invoice.invoice_number} L{self.line_number} – {label}"
    
    @override
    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Must be greater than zero."})
        if self.item_id and self.item.requires_batch() and not self.batch_id:
            raise ValidationError({"batch": "Required for batch-tracked items."})


class Payment(BaseModel):
    class PaymentType(models.TextChoices):
        RECEIPT = "receipt", "Customer Receipt"
        DISBURSEMENT = "disbursement", "Vendor Disbursement"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CHECK = "check", "Check"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CREDIT_CARD = "credit_card", "Credit Card"
        ONLINE = "online", "Online"
        OTHER = "other", "Other"

    payment_number = models.CharField(max_length=30, unique=True)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    customer = models.ForeignKey(
        Customer, null=True, blank=True, on_delete=models.PROTECT, related_name="payments"
    )
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.PROTECT, related_name="payment"
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=_DP)
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_payment"
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["payment_type"]),
            models.Index(fields=["payment_date"]),
        ]
    
    @override
    def __str__(self):
        return f"{self.payment_number} ({self.payment_type}) {self.amount}"
    
    @override
    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Must be positive."})
        if self.payment_type == self.PaymentType.RECEIPT and not self.customer_id:
            raise ValidationError({"customer": "Required for receipt payments."})
    
    @override
    def save(self, *args, **kwargs):
        from django_accounting.signals import payment_received, disbursement_made
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            if self.payment_type == self.PaymentType.RECEIPT:
                payment_received.send(sender=self.__class__, payment=self)
            else:
                disbursement_made.send(sender=self.__class__, payment=self)


class InvoicePayment(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payment_allocations")
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="invoice_allocations")
    applied_amount = models.DecimalField(max_digits=18, decimal_places=_DP)

    class Meta(BaseModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_invoice_payment"
        unique_together = [("invoice", "payment")]
    
    @override
    def __str__(self):
        return f"{self.payment.payment_number} → {self.invoice.invoice_number} : {self.applied_amount}"

    @override
    def clean(self):
        if self.applied_amount is not None and self.applied_amount <= 0:
            raise ValidationError({"applied_amount": "Must be positive."})

    @override
    def save(self, *args, **kwargs):
        from ..signals import payment_applied
        super().save(*args, **kwargs)
        payment_applied.send(
            sender=self.__class__,
            payment=self.payment, invoice=self.invoice, applied_amount=self.applied_amount,
        )
