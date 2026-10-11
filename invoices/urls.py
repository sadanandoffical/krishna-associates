from django.urls import path
from rest_framework.routers import DefaultRouter

from .customer_invoice_view import CustomerInvoiceHistoryView
from .views import (
    InvoiceBulkPDFView,
    InvoiceViewSet,
    InvoicePDFView
)


router = DefaultRouter()

router.register(
    "",
    InvoiceViewSet,
    basename="invoice",
)


urlpatterns = [
    path(
        "bulk-pdf/",
        InvoiceBulkPDFView.as_view(),
        name="invoice-bulk-pdf",
    ),
    path(
        "customer/<int:customer_id>/",
        CustomerInvoiceHistoryView.as_view(),
        name="customer-invoice-history",
    ),
    path(
        "<int:invoice_id>/pdf/",
        InvoicePDFView.as_view(),
        name="invoice-pdf",
    ),
]

urlpatterns += router.urls