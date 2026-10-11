from rest_framework import serializers

from .models import Enquiry


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = [
            "name",
            "phone",
            "requirement",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Name cannot be empty."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Phone cannot be empty."
            )

        return value

    def validate_requirement(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Requirement cannot be empty."
            )

        return value