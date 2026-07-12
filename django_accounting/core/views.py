# django_accounting/core/views.py

from rest_framework import generics, filters
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, FiscalYear, FiscalPeriod
from .serializers import (
    AccountSerializer,
    AccountTreeSerializer,
    FiscalYearSerializer,
    FiscalYearListSerializer,
    FiscalPeriodSerializer,
)


# ── Account ───────────────────────────────────────────────────────────────────

class AccountListCreateView(generics.ListCreateAPIView):
    queryset = Account.objects.select_related("parent").order_by("code")
    serializer_class = AccountSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name", "type"]
    filterset_fields = ["type", "is_active", "parent"]


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.select_related("parent").order_by("code")
    serializer_class = AccountSerializer


class AccountTreeView(APIView):
    """Returns the full chart of accounts as a nested tree."""

    def get(self, request: Request) -> Response:
        roots = Account.objects.filter(parent=None, is_active=True)
        serializer = AccountTreeSerializer(
            roots, many=True, context={"request": request}
        )
        return Response(serializer.data)


# ── FiscalYear ────────────────────────────────────────────────────────────────

class FiscalYearListCreateView(generics.ListCreateAPIView):
    queryset = FiscalYear.objects.prefetch_related("periods").order_by("-year")
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["year", "start_date"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return FiscalYearListSerializer
        return FiscalYearSerializer


class FiscalYearDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FiscalYear.objects.prefetch_related("periods").order_by("-year")
    serializer_class = FiscalYearSerializer


# ── FiscalPeriod ──────────────────────────────────────────────────────────────

class FiscalPeriodListCreateView(generics.ListCreateAPIView[FiscalPeriod]):
    queryset = FiscalPeriod.objects.select_related("fiscal_year").order_by("start_date")
    serializer_class = FiscalPeriodSerializer
    filterset_fields = ["fiscal_year", "is_closed"]


class FiscalPeriodDetailView(generics.RetrieveUpdateDestroyAPIView[FiscalPeriod]):
    queryset = FiscalPeriod.objects.select_related("fiscal_year")
    serializer_class = FiscalPeriodSerializer
