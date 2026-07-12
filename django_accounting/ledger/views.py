from rest_framework import generics, filters

from .models import JournalEntry, JournalLine
from .serializers import (
    JournalEntrySerializer,
    JournalEntryWriteSerializer,
    JournalEntryListSerializer,
    JournalLineSerializer,
)


class JournalEntryListCreateView(generics.ListCreateAPIView):
    queryset = (
        JournalEntry.objects
        .select_related("fiscal_period", "created_by", "approved_by")
        .prefetch_related("lines__account")
        .order_by("-entry_date")
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["entry_number", "description"]
    ordering_fields = ["entry_date", "status"]
    filterset_fields = ["status", "fiscal_period", "entry_date"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return JournalEntryWriteSerializer
        return JournalEntryListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class JournalEntryDetailView(generics.RetrieveUpdateDestroyAPIView[JournalEntry]):
    queryset = (
        JournalEntry.objects
        .select_related("fiscal_period", "created_by", "approved_by")
        .prefetch_related("lines__account")
    )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return JournalEntryWriteSerializer
        return JournalEntrySerializer


class JournalLineListCreateView(generics.ListCreateAPIView[JournalLine]):
    serializer_class = JournalLineSerializer

    def get_queryset(self):
        return JournalLine.objects.filter(
            journal_entry_id=self.kwargs["entry_id"]
        ).select_related("account")


class JournalLineDetailView(generics.RetrieveUpdateDestroyAPIView[JournalLine]):
    serializer_class = JournalLineSerializer

    def get_queryset(self):
        return JournalLine.objects.filter(
            journal_entry_id=self.kwargs["entry_id"]
        ).select_related("account")
