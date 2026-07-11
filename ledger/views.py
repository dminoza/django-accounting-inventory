"""
django_accounting/ledger/views.py
"""

from rest_framework import viewsets

from .models import JournalEntry
from .serializers import (
    JournalEntrySerializer,
    JournalEntryWriteSerializer,
    JournalEntryListSerializer,
)


class JournalEntryViewSet(viewsets.ModelViewSet[JournalEntry]):
    queryset = (
        JournalEntry.objects
        .select_related("fiscal_period", "created_by", "approved_by")
        .prefetch_related("lines__account")
        .order_by("-entry_date")
    )
    filterset_fields = ["status", "fiscal_period", "entry_date"]
    search_fields = ["entry_number", "description"]

    def get_serializer_class(self):
        if self.action == "list":
            return JournalEntryListSerializer
        if self.action in ("create", "update", "partial_update"):
            return JournalEntryWriteSerializer
        return JournalEntrySerializer
