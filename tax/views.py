"""
django_accounting/tax/views.py
"""

from rest_framework import viewsets

from .models import TaxAuthority, TaxRate, TaxGroup, TaxLine
from .serializers import (
    TaxAuthoritySerializer,
    TaxRateSerializer,
    TaxGroupSerializer,
    TaxGroupWriteSerializer,
    TaxLineSerializer,
)


class TaxAuthorityViewSet(viewsets.ModelViewSet[TaxAuthority]):
    queryset = TaxAuthority.objects.select_related(
        "tax_payable_account", "tax_receivable_account"
    ).order_by("code")
    serializer_class = TaxAuthoritySerializer
    filterset_fields = ["is_active"]
    search_fields = ["code", "name"]


class TaxRateViewSet(viewsets.ModelViewSet[TaxRate]):
    queryset = TaxRate.objects.select_related("tax_authority").order_by("code")
    serializer_class = TaxRateSerializer
    filterset_fields = ["tax_type", "is_active", "is_compound", "tax_authority"]
    search_fields = ["code", "name"]


class TaxGroupViewSet(viewsets.ModelViewSet[TaxGroup]):
    queryset = (
        TaxGroup.objects
        .prefetch_related("group_rates__tax_rate")
        .order_by("code")
    )
    filterset_fields = ["is_active"]
    search_fields = ["code", "name"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TaxGroupWriteSerializer
        return TaxGroupSerializer
