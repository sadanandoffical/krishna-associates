from django.contrib import admin

from .models import Site, SiteFeature, SiteMedia


class SiteMediaInline(admin.TabularInline):
    model = SiteMedia
    extra = 1


class SiteFeatureInline(admin.TabularInline):
    model = SiteFeature
    extra = 1


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "city",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "address",
    )

    list_filter = (
        "city",
    )

    inlines = (
        SiteMediaInline,
        SiteFeatureInline,
    )


@admin.register(SiteMedia)
class SiteMediaAdmin(admin.ModelAdmin):
    list_display = (
        "site",
        "media_type",
        "ordering",
    )

    list_filter = (
        "media_type",
    )


@admin.register(SiteFeature)
class SiteFeatureAdmin(admin.ModelAdmin):
    list_display = (
        "site",
        "label",
        "value",
        "ordering",
    )

    search_fields = (
        "label",
        "value",
    )