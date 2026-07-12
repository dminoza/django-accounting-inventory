from typing import Any, ClassVar, override

from django.core.exceptions import ValidationError
from django.db import models

from ..mixins import BaseActiveModel, BaseModel
from ..signals import account_created



class Account(BaseActiveModel):
    class AccountType(models.TextChoices):
        ASSET = "asset", "Asset"
        LIABILITY = "liability", "Liability"
        EQUITY = "equity", "Equity"
        REVENUE = "revenue", "Revenue"
        EXPENSE = "expense", "Expense"

    class NormalBalance(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=AccountType.choices)
    normal_balance = models.CharField(max_length=10, choices=NormalBalance.choices)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children"
    )
    description = models.TextField(blank=True)
    children: ClassVar[models.Manager[Account]]

    class Meta(BaseActiveModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_acount"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["is_active"]),
        ]
    
    @override
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
    
    @override
    def clean(self):
        if self.parent and self.parent.pk == self.id:
            raise ValidationError("An Account cannot be its own parent")
        debit_types = {self.AccountType.ASSET, self.AccountType.EXPENSE}
        if self.type and self.normal_balance:
            expected = (
                self.NormalBalance.DEBIT
                if self.type in debit_types
                else self.NormalBalance.CREDIT
            )
            if self.normal_balance != expected:
                raise ValidationError(
                    {"normal_balance" : f"Type '{self.type}' requires '{expected}'."}
                )
    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            account_created.send(sender=self.__class__, account=self)


class FiscalYear(BaseModel):
    year = models.PositiveIntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)


    class Meta(BaseModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_fiscal_year"
        ordering = ["-year"]
    
    @override
    def __str__(self) -> str:
        return f"FY {self.year}"

    @override
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({"end_date" : "end_date must be after start_date."})

class FiscalPeriod(BaseModel):
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.PROTECT, related_name="periods"
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        app_label = "django_accounting"
        db_table = "accounting_fiscal_year_period"
        ordering = ["start_date"]
        unique_together = [("fiscal_year", "name")]
        indexes = [models.Index(fields=["start_date", "end_date"])]
    
    @override
    def __str__(self) -> str:
        return f"{self.fiscal_year} / {self.name}"

    @override
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({"end_date" : "end_date must be after start_date"})


