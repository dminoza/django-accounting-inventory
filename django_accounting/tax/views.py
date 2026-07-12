from rest_framework import generics, filters

from .models import TaxAuthority, TaxRate, TaxGroup, TaxLine
from .serializers import (
    TaxAuthoritySerializer,
    TaxRateSerializer,
    TaxGroupSerializer,
    TaxGroupWriteSerializer,
    TaxLineSerializer,
)


class TaxAuthorityListCreateView(generics.ListCreateAPIView):
    queryset = TaxAuthority.objects.select_related(
        "tax_payable_account", "tax_receivable_account"
    ).order_by("code")
    serializer_class = TaxAuthoritySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]
    filterset_fields = ["is_active"]


class TaxAuthorityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaxAuthority.objects.select_related(
        "tax_payable_account", "tax_receivable_account"
    )
    serializer_class = TaxAuthoritySerializer


class TaxRateListCreateView(generics.ListCreateAPIView):
    queryset = TaxRate.objects.select_related("tax_authority").order_by("code")
    serializer_class = TaxRateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]
    filterset_fields = ["tax_type", "is_active", "is_compound", "tax_authority"]


class TaxRateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaxRate.objects.select_related("tax_authority")
    serializer_class = TaxRateSerializer


class TaxGroupListCreateView(generics.ListCreateAPIView):
    queryset = TaxGroup.objects.prefetch_related("group_rates__tax_rate").order_by("code")
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "name"]
    filterset_fields = ["is_active"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaxGroupWriteSerializer
        return TaxGroupSerializer


class TaxGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaxGroup.objects.prefetch_related("group_rates__tax_rate")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TaxGroupWriteSerializer
        return TaxGroupSerializer


class TaxLineListCreateView(generics.ListCreateAPIView):
    queryset = TaxLine.objects.select_related("tax_rate").order_by("-created_at")
    serializer_class = TaxLineSerializer
    filterset_fields = ["source_type", "tax_rate"]
