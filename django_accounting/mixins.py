"""
django_accounting/mixins.py

Abstract model mixins — compose these onto any model.
All mixins use abstract = True so they never create their own table.
"""

import uuid
from django.db import models
from django.utils import timezone


# ── Identity & timestamps ──────────────────────────────────────────────────────

class UUIDPrimaryKeyMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveMixin(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


# ── Soft delete ────────────────────────────────────────────────────────────────

class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteMixin(models.Model):
    """
    Replace hard-deletes with a flag.
    Enabled when ACCOUNTING['ENABLE_SOFT_DELETE'] = True.
    Models using this mixin get .objects.alive() and .objects.with_deleted().
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # bypass soft-delete filter

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        from django_accounting.conf import accounting_settings
        if accounting_settings.ENABLE_SOFT_DELETE:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


# ── Currency ───────────────────────────────────────────────────────────────────

class CurrencyMixin(models.Model):
    """Adds a currency field defaulting to ACCOUNTING['DEFAULT_CURRENCY']."""

    def _default_currency():  # noqa: N805 — used as a callable default
        from django_accounting.conf import accounting_settings
        return accounting_settings.DEFAULT_CURRENCY

    currency = models.CharField(max_length=3, default=_default_currency)

    class Meta:
        abstract = True


# ── Convenience composite base ─────────────────────────────────────────────────

class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, models.Model):
    """Minimal base: UUID PK + created_at/updated_at."""

    class Meta:
        abstract = True


class BaseActiveModel(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin, models.Model):
    """Base + is_active flag."""

    class Meta:
        abstract = True


class BaseDocumentModel(UUIDPrimaryKeyMixin, TimestampMixin, CurrencyMixin, models.Model):
    """
    Base for financial documents (Invoice, Bill, JournalEntry).
    Includes UUID PK, timestamps, and currency.
    """

    class Meta:
        abstract = True
