from rest_framework import serializers

from cities.models import City
from .models import Site, SiteMedia, SiteFeature
from .validators import validate_media_file,validate_map_image


class SiteMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteMedia
        fields = [
            "id",
            "media_type",
            "file",
            "ordering",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_media_type(self, value):
        allowed_types = {
            SiteMedia.IMAGE,
            SiteMedia.VIDEO,
        }

        if value not in allowed_types:
            raise serializers.ValidationError(
                "Media type must be either image or video."
            )

        return value

    def validate_ordering(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Ordering cannot be negative."
            )

        return value

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError(
                "A media file is required."
            )

        max_size = 50 * 1024 * 1024  # 50 MB

        if value.size > max_size:
            raise serializers.ValidationError(
                "Media file cannot exceed 50 MB."
            )

        media_type = self.initial_data.get(
            "media_type"
        )

        validate_media_file(
            media_type,
            value,
        )

        return value


class SiteFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteFeature
        fields = [
            "id",
            "label",
            "value",
            "ordering",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_label(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Feature label cannot be empty."
            )

        return value

    def validate_value(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Feature value cannot be empty."
            )

        return value


class SiteListSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(
        source="city.name",
        read_only=True,
    )

    class Meta:
        model = Site
        fields = [
            "id",
            "title",
            "address",
            "city",
            "city_name",
            "map_image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class SiteDetailSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(
        source="city.name",
        read_only=True,
    )

    media = SiteMediaSerializer(
        many=True,
        read_only=True,
    )

    features = SiteFeatureSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Site
        fields = [
            "id",
            "city",
            "city_name",
            "title",
            "address",
            "description",
            "map_image",
            "media",
            "features",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "media",
            "features",
        ]


class SiteWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            "id",
            "city",
            "title",
            "address",
            "description",
            "map_image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Site title cannot be empty."
            )

        return value

    def validate_address(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Site address cannot be empty."
            )

        return value

    def validate_city(self, value):
        if not isinstance(value, City):
            raise serializers.ValidationError(
                "A valid city is required."
            )

        return value

    def validate_map_image(self, value):
        if value:
            return validate_map_image(value)

        return value