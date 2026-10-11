from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(
        source="city.name",
        read_only=True,
    )

    associate_name = serializers.CharField(
        source="associate.name",
        read_only=True,
    )

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "city",
            "city_name",
            "associate",
            "associate_name",
            "emi_start_date",
            "address",
            "project",
            "plot_area",
            "plot_rate",
            "plot_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "city_name",
            "associate_name",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Customer name cannot be empty."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Customer phone cannot be empty."
            )

        return value