from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import SiteFeatureViewSet, SiteMediaViewSet, SiteViewSet


router = DefaultRouter()

router.register(
    "",
    SiteViewSet,
    basename="site",
)

# features_router = NestedDefaultRouter(
#     router,
#     "",
#     lookup="site",
# )

# features_router.register(
#     "features",
#     SiteFeatureViewSet,
#     basename="site-features",
# )

nested_router = NestedDefaultRouter(
    router,
    "",
    lookup="site",
)

nested_router.register(
    "features",
    SiteFeatureViewSet,
    basename="site-features",
)

nested_router.register(
    "media",
    SiteMediaViewSet,
    basename="site-media",
)


urlpatterns = (
    router.urls
    + nested_router.urls
)