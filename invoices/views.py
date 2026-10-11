from django.db import IntegrityError
from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters,status, viewsets
from rest_framework.response import Response

from accounts.permissions import IsAdminUser
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .filters import InvoiceFilter
from .models import Invoice
from .serializers import InvoiceSerializer
from .pdf import InvoicePDFError, render_invoice_pdf
from rest_framework.views import APIView

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminUser]

    queryset = Invoice.objects.select_related(
        "customer",
    )

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]

    filterset_class = InvoiceFilter

    search_fields = [
        "invoice_number",
    ]

    def destroy(self, request, *args, **kwargs):
        invoice = self.get_object()

        try:
            invoice.delete()

        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "This invoice cannot be deleted because "
                        "it is referenced by existing records."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This invoice cannot be deleted because "
                        "it is referenced by existing records."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class InvoicePDFView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, invoice_id):
        invoice = get_object_or_404(
            Invoice.objects.select_related("customer"),
            id=invoice_id,
        )

        try:
            pdf_bytes = render_invoice_pdf(invoice)

        except InvoicePDFError:
            return Response(
                {
                    "detail": (
                        "Unable to generate PDF for "
                        f"invoice {invoice.invoice_number}."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response[
            "Content-Disposition"
        ] = (
            f'attachment; '
            f'filename="{invoice.invoice_number}.pdf"'
        )

        return response

class InvoiceBulkPDFView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        raw_ids = request.query_params.get("ids", "")

        if not raw_ids.strip():
            return Response(
                {
                    "detail": (
                        "At least one invoice ID is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_id_list = [
            value.strip()
            for value in raw_ids.split(",")
            if value.strip()
        ]

        if not raw_id_list:
            return Response(
                {
                    "detail": (
                        "At least one invoice ID is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invalid_ids = [
            value
            for value in raw_id_list
            if not value.isdigit()
        ]

        if invalid_ids:
            return Response(
                {
                    "detail": (
                        "Invoice IDs must be positive integers."
                    ),
                    "invalid_ids": invalid_ids,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_ids = list(
            dict.fromkeys(
                int(value)
                for value in raw_id_list
            )
        )

        invoices = list(
            Invoice.objects
            .select_related("customer")
            .filter(id__in=invoice_ids)
        )

        found_ids = {
            invoice.id
            for invoice in invoices
        }

        missing_ids = [
            invoice_id
            for invoice_id in invoice_ids
            if invoice_id not in found_ids
        ]

        if missing_ids:
            return Response(
                {
                    "detail": (
                        "One or more requested invoices "
                        "were not found."
                    ),
                    "missing_ids": missing_ids,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        invoices_by_id = {
            invoice.id: invoice
            for invoice in invoices
        }

        output = BytesIO()

        try:
            with ZipFile(
                output,
                mode="w",
                compression=ZIP_DEFLATED,
            ) as archive:

                for invoice_id in invoice_ids:
                    invoice = invoices_by_id[
                        invoice_id
                    ]

                    try:
                        pdf_bytes = render_invoice_pdf(
                            invoice
                        )
                    except InvoicePDFError:
                        return Response(
                            {
                                "detail": (
                                    "Unable to generate PDF for "
                                    f"invoice {invoice.invoice_number}."
                                ),
                                "invoice_id": invoice.id,
                                "invoice_number": (
                                    invoice.invoice_number
                                ),
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    archive.writestr(
                        f"{invoice.invoice_number}.pdf",
                        pdf_bytes,
                    )

        except Exception:
            return Response(
                {
                    "detail": (
                        "Unable to generate the invoice export."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(
            output.getvalue(),
            content_type="application/zip",
        )

        response[
            "Content-Disposition"
        ] = 'attachment; filename="invoices.zip"'

        return response