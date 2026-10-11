from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer",
        "payee_name",
        "amount",
        "invoice_date",
        "status",
        "created_at",
    )

    search_fields = (
        "invoice_number",
        "payee_name",
    )

    list_filter = (
        "status",
        "customer",
        "created_at",
    )

    readonly_fields = (
        "invoice_number",
        "created_at",
        "updated_at",
    )