from django.db import IntegrityError
from django.db.models import ProtectedError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.response import Response

from accounts.api_permissions import IsAdminOrReadOnly

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrReadOnly]

    queryset = Customer.objects.select_related(
        "city",
        "associate",
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get("search")
        if search:
            search = search.strip()

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search)
                    | Q(phone__icontains=search)
                )

        city = self.request.query_params.get("city")
        if city:
            queryset = queryset.filter(city_id=city)

        associate = self.request.query_params.get("associate")
        if associate:
            queryset = queryset.filter(associate_id=associate)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        Return a single customer with its related city/associate
        data already optimized through select_related().
        """
        customer = self.get_object()

        serializer = self.get_serializer(customer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()

        try:
            customer.delete()

        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "This customer cannot be deleted because "
                        "they have existing invoices."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This customer cannot be deleted because "
                        "it is referenced by existing records."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)