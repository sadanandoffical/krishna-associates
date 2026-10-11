from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AssociateProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Krishna Associates",
            {
                "fields": ("role",),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "role",
        "is_staff",
        "is_active",
    )


@admin.register(AssociateProfile)
class AssociateProfileAdmin(admin.ModelAdmin):
    list_display = (
        "associate_id",
        "name",
        "email",
        "phone",
        "user",
    )

    search_fields = (
        "associate_id",
        "name",
        "email",
        "phone",
    )