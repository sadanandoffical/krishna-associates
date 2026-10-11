from rest_framework import status, viewsets
from rest_framework.response import Response

from accounts.api_permissions import IsAdminOrReadOnly

from .models import Site, SiteFeature, SiteMedia
from .serializers import (
    SiteDetailSerializer,
    SiteFeatureSerializer,
    SiteListSerializer,
    SiteWriteSerializer,
    SiteMediaSerializer
)


class SiteViewSet(viewsets.ModelViewSet):
    queryset = (
        Site.objects
        .select_related("city")
        .prefetch_related(
            "media",
            "features",
        )
    )

    permission_classes = [
        IsAdminOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return SiteListSerializer

        if self.action == "retrieve":
            return SiteDetailSerializer

        return SiteWriteSerializer


class SiteFeatureViewSet(viewsets.ModelViewSet):
    serializer_class = SiteFeatureSerializer
    permission_classes = [
        IsAdminOrReadOnly,
    ]

    def get_queryset(self):
        return SiteFeature.objects.filter(
            site_id=self.kwargs["site_pk"]
        ).select_related("site")

    def perform_create(self, serializer):
        site = Site.objects.get(
            pk=self.kwargs["site_pk"]
        )

        serializer.save(site=site)

    def create(self, request, *args, **kwargs):
        # Explicitly verify that the parent Site exists.
        site_id = kwargs["site_pk"]

        if not Site.objects.filter(
            pk=site_id
        ).exists():
            return Response(
                {
                    "detail": "Site not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return super().create(
            request,
            *args,
            **kwargs,
        )

class SiteMediaViewSet(viewsets.ModelViewSet):
    serializer_class = SiteMediaSerializer
    permission_classes = [
        IsAdminOrReadOnly,
    ]

    def get_queryset(self):
        return SiteMedia.objects.filter(
            site_id=self.kwargs["site_pk"]
        ).select_related("site")

    def perform_create(self, serializer):
        site = Site.objects.get(
            pk=self.kwargs["site_pk"]
        )

        serializer.save(
            site=site
        )

    def create(self, request, *args, **kwargs):
        site_id = kwargs["site_pk"]

        if not Site.objects.filter(
            pk=site_id
        ).exists():
            return Response(
                {
                    "detail": "Site not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return super().create(
            request,
            *args,
            **kwargs,
        )