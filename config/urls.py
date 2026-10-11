from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/accounts/", include("accounts.urls")),
    path("api/cities/", include("cities.urls")),
    path("api/sites/", include("sites.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/invoices/", include("invoices.urls")),
    path("api/enquiries/", include("enquiries.urls")),
    path("", include("web.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )