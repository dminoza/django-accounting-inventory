from django.urls import path

from .core.views import (
    AccountListCreateView, AccountDetailView, AccountTreeView,
    FiscalYearListCreateView, FiscalYearDetailView,
    FiscalPeriodListCreateView, FiscalPeriodDetailView,
)
from .ledger.views import (
    JournalEntryListCreateView, JournalEntryDetailView,
    JournalLineListCreateView, JournalLineDetailView,
)
from .tax.views import (
    TaxAuthorityListCreateView, TaxAuthorityDetailView,
    TaxRateListCreateView, TaxRateDetailView,
    TaxGroupListCreateView, TaxGroupDetailView,
    TaxLineListCreateView,
)
from .inventory.views import (
    ItemCategoryListCreateView, ItemCategoryDetailView,
    ItemListCreateView, ItemDetailView,
    ItemBatchListCreateView, ItemBatchDetailView,
    ItemBatchExpiringSoonView,
    WarehouseListCreateView, WarehouseDetailView,
    WarehouseLocationListCreateView, WarehouseLocationDetailView,
    InventoryBalanceListView, InventoryBalanceDetailView,
    InventoryMovementListCreateView, InventoryMovementDetailView,
)
from .ar.views import (
    CustomerListCreateView, CustomerDetailView,
    InvoiceListCreateView, InvoiceDetailView,
    InvoiceLineListCreateView, InvoiceLineDetailView,
    PaymentListCreateView, PaymentDetailView,
    InvoicePaymentListCreateView, InvoicePaymentDetailView,
)
from .ap.views import (
    VendorListCreateView, VendorDetailView,
    BillListCreateView, BillDetailView,
    BillLineListCreateView, BillLineDetailView,
    BillPaymentListCreateView, BillPaymentDetailView,
)

urlpatterns = [
    # ── Core ─────────────────────────────────────────────────────────────────
    path("accounts/",                    AccountListCreateView.as_view(),     name="account-list"),
    path("accounts/tree/",               AccountTreeView.as_view(),           name="account-tree"),
    path("accounts/<uuid:pk>/",          AccountDetailView.as_view(),         name="account-detail"),
    path("fiscal-years/",                FiscalYearListCreateView.as_view(),  name="fiscal-year-list"),
    path("fiscal-years/<uuid:pk>/",      FiscalYearDetailView.as_view(),      name="fiscal-year-detail"),
    path("fiscal-periods/",              FiscalPeriodListCreateView.as_view(), name="fiscal-period-list"),
    path("fiscal-periods/<uuid:pk>/",    FiscalPeriodDetailView.as_view(),    name="fiscal-period-detail"),

    # ── Ledger ────────────────────────────────────────────────────────────────
    path("journal-entries/",             JournalEntryListCreateView.as_view(),  name="journal-entry-list"),
    path("journal-entries/<uuid:pk>/",   JournalEntryDetailView.as_view(),      name="journal-entry-detail"),
    path("journal-entries/<uuid:entry_id>/lines/",          JournalLineListCreateView.as_view(), name="journal-line-list"),
    path("journal-entries/<uuid:entry_id>/lines/<uuid:pk>/", JournalLineDetailView.as_view(),   name="journal-line-detail"),

    # ── Tax ───────────────────────────────────────────────────────────────────
    path("tax-authorities/",             TaxAuthorityListCreateView.as_view(), name="tax-authority-list"),
    path("tax-authorities/<uuid:pk>/",   TaxAuthorityDetailView.as_view(),     name="tax-authority-detail"),
    path("tax-rates/",                   TaxRateListCreateView.as_view(),      name="tax-rate-list"),
    path("tax-rates/<uuid:pk>/",         TaxRateDetailView.as_view(),          name="tax-rate-detail"),
    path("tax-groups/",                  TaxGroupListCreateView.as_view(),     name="tax-group-list"),
    path("tax-groups/<uuid:pk>/",        TaxGroupDetailView.as_view(),         name="tax-group-detail"),
    path("tax-lines/",                   TaxLineListCreateView.as_view(),      name="tax-line-list"),

    # ── Inventory ─────────────────────────────────────────────────────────────
    path("item-categories/",             ItemCategoryListCreateView.as_view(), name="item-category-list"),
    path("item-categories/<uuid:pk>/",   ItemCategoryDetailView.as_view(),     name="item-category-detail"),
    path("items/",                       ItemListCreateView.as_view(),         name="item-list"),
    path("items/<uuid:pk>/",             ItemDetailView.as_view(),             name="item-detail"),
    path("item-batches/",                ItemBatchListCreateView.as_view(),    name="item-batch-list"),
    path("item-batches/expiring-soon/",  ItemBatchExpiringSoonView.as_view(),  name="item-batch-expiring"),
    path("item-batches/<uuid:pk>/",      ItemBatchDetailView.as_view(),        name="item-batch-detail"),
    path("warehouses/",                  WarehouseListCreateView.as_view(),    name="warehouse-list"),
    path("warehouses/<uuid:pk>/",        WarehouseDetailView.as_view(),        name="warehouse-detail"),
    path("warehouse-locations/",         WarehouseLocationListCreateView.as_view(), name="warehouse-location-list"),
    path("warehouse-locations/<uuid:pk>/", WarehouseLocationDetailView.as_view(),  name="warehouse-location-detail"),
    path("inventory-balances/",          InventoryBalanceListView.as_view(),   name="inventory-balance-list"),
    path("inventory-balances/<uuid:pk>/", InventoryBalanceDetailView.as_view(), name="inventory-balance-detail"),
    path("inventory-movements/",         InventoryMovementListCreateView.as_view(), name="inventory-movement-list"),
    path("inventory-movements/<uuid:pk>/", InventoryMovementDetailView.as_view(),  name="inventory-movement-detail"),

    # ── AR ────────────────────────────────────────────────────────────────────
    path("customers/",                   CustomerListCreateView.as_view(),     name="customer-list"),
    path("customers/<uuid:pk>/",         CustomerDetailView.as_view(),         name="customer-detail"),
    path("invoices/",                    InvoiceListCreateView.as_view(),      name="invoice-list"),
    path("invoices/<uuid:pk>/",          InvoiceDetailView.as_view(),          name="invoice-detail"),
    path("invoices/<uuid:invoice_id>/lines/",          InvoiceLineListCreateView.as_view(), name="invoice-line-list"),
    path("invoices/<uuid:invoice_id>/lines/<uuid:pk>/", InvoiceLineDetailView.as_view(),   name="invoice-line-detail"),
    path("payments/",                    PaymentListCreateView.as_view(),      name="payment-list"),
    path("payments/<uuid:pk>/",          PaymentDetailView.as_view(),          name="payment-detail"),
    path("invoice-payments/",            InvoicePaymentListCreateView.as_view(), name="invoice-payment-list"),
    path("invoice-payments/<uuid:pk>/",  InvoicePaymentDetailView.as_view(),   name="invoice-payment-detail"),

    # ── AP ────────────────────────────────────────────────────────────────────
    path("vendors/",                     VendorListCreateView.as_view(),       name="vendor-list"),
    path("vendors/<uuid:pk>/",           VendorDetailView.as_view(),           name="vendor-detail"),
    path("bills/",                       BillListCreateView.as_view(),         name="bill-list"),
    path("bills/<uuid:pk>/",             BillDetailView.as_view(),             name="bill-detail"),
    path("bills/<uuid:bill_id>/lines/",          BillLineListCreateView.as_view(), name="bill-line-list"),
    path("bills/<uuid:bill_id>/lines/<uuid:pk>/", BillLineDetailView.as_view(),   name="bill-line-detail"),
    path("bill-payments/",               BillPaymentListCreateView.as_view(),  name="bill-payment-list"),
    path("bill-payments/<uuid:pk>/",     BillPaymentDetailView.as_view(),      name="bill-payment-detail"),
]
