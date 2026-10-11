import django_filters

from .models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    customer = django_filters.NumberFilter(
        field_name="customer_id"
    )

    status = django_filters.CharFilter(
        field_name="status"
    )

    created_at = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date",
    )

    created_at_after = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
    )

    created_at_before = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
    )

    class Meta:
        model = Invoice
        fields = [
            "customer",
            "status",
            "created_at",
            "created_at_after",
            "created_at_before",
        ]