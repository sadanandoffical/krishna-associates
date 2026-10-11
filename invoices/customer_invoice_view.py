from django.shortcuts import get_object_or_404

from rest_framework import generics

from accounts.permissions import IsAdminUser
from customers.models import Customer

from .models import Invoice
from .serializers import CustomerInvoiceHistorySerializer


class CustomerInvoiceHistoryView(generics.ListAPIView):
    serializer_class = CustomerInvoiceHistorySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        customer_id = self.kwargs["customer_id"]

        # Explicitly validate that the customer exists.
        get_object_or_404(
            Customer,
            pk=customer_id,
        )

        return (
            Invoice.objects
            .filter(customer_id=customer_id)
            .order_by("-invoice_date", "-id")
        )