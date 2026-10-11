from django.contrib import admin

from .models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "requirement",
    )

    readonly_fields = (
        "created_at",
    )