"""
django_accounting/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .core.views import AccountViewSet, FiscalYearViewSet, FiscalPeriodViewSet
from .ledger.views import JournalEntryViewSet
from .tax.views import TaxAuthorityViewSet, TaxRateViewSet, TaxGroupViewSet
from .inventory.views import (
    ItemCategoryViewSet, ItemViewSet, ItemBatchViewSet,
    WarehouseViewSet, WarehouseLocationViewSet,
    InventoryBalanceViewSet, InventoryMovementViewSet,
)
from .ar.views import CustomerViewSet, InvoiceViewSet, PaymentViewSet, InvoicePaymentViewSet
from .ap.views import VendorViewSet, BillViewSet, BillPaymentViewSet

router = DefaultRouter()

# Core
router.register("accounts", AccountViewSet, basename="account")
router.register("fiscal-years", FiscalYearViewSet, basename="fiscal-year")
router.register("fiscal-periods", FiscalPeriodViewSet, basename="fiscal-period")

# Ledger
router.register("journal-entries", JournalEntryViewSet, basename="journal-entry")

# Tax
router.register("tax-authorities", TaxAuthorityViewSet, basename="tax-authority")
router.register("tax-rates", TaxRateViewSet, basename="tax-rate")
router.register("tax-groups", TaxGroupViewSet, basename="tax-group")

# Inventory
router.register("item-categories", ItemCategoryViewSet, basename="item-category")
router.register("items", ItemViewSet, basename="item")
router.register("item-batches", ItemBatchViewSet, basename="item-batch")
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("warehouse-locations", WarehouseLocationViewSet, basename="warehouse-location")
router.register("inventory-balances", InventoryBalanceViewSet, basename="inventory-balance")
router.register("inventory-movements", InventoryMovementViewSet, basename="inventory-movement")

# AR
router.register("customers", CustomerViewSet, basename="customer")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")
router.register("invoice-payments", InvoicePaymentViewSet, basename="invoice-payment")

# AP
router.register("vendors", VendorViewSet, basename="vendor")
router.register("bills", BillViewSet, basename="bill")
router.register("bill-payments", BillPaymentViewSet, basename="bill-payment")

urlpatterns = [path("", include(router.urls))]
