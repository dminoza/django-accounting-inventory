"""
django_accounting/core/views.py
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Account, FiscalYear, FiscalPeriod
from .serializers import (
    AccountSerializer,
    AccountTreeSerializer,
    FiscalYearSerializer,
    FiscalYearListSerializer,
    FiscalPeriodSerializer,
)


class AccountViewSet(viewsets.ModelViewSet[Account]):
    queryset = Account.objects.select_related("parent").order_by("code")
    serializer_class = AccountSerializer
    filterset_fields = ["type", "is_active", "parent"]
    search_fields = ["code", "name"]

    def get_serializer_class(self):
        if self.action == "tree":
            return AccountTreeSerializer
        return AccountSerializer

    @action(detail=False, methods=["get"])
    def tree(self, request: Request) -> Response:
        """Returns top-level accounts with recursively nested children."""
        roots = Account.objects.filter(parent=None, is_active=True)
        serializer = AccountTreeSerializer(roots, many=True)
        return Response(serializer.data)


class FiscalYearViewSet(viewsets.ModelViewSet[FiscalYear]):
    queryset = FiscalYear.objects.prefetch_related("periods").order_by("-year")

    def get_serializer_class(self):
        if self.action == "list":
            return FiscalYearListSerializer
        return FiscalYearSerializer


class FiscalPeriodViewSet(viewsets.ModelViewSet[FiscalPeriod]):
    queryset = FiscalPeriod.objects.select_related("fiscal_year").order_by("start_date")
    serializer_class = FiscalPeriodSerializer
    filterset_fields = ["fiscal_year", "is_closed"]
