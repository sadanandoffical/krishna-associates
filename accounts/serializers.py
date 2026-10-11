import secrets
import string
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import AssociateProfile, User
from .services import create_associate



class AssociateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociateProfile
        fields = [
            "id",
            "associate_id",
            "name",
            "email",
            "phone",
            "picture",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "associate_id",
            "created_at",
            "updated_at",
        ]

class AdminAssociateListSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(
        source="user.is_active",
        read_only=True,
    )

    class Meta:
        model = AssociateProfile
        fields = [
            "id",
            "associate_id",
            "name",
            "email",
            "phone",
            "picture",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AssociateLoginSerializer(serializers.Serializer):
    associate_id = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        associate_id = attrs["associate_id"].strip()
        password = attrs["password"]

        try:
            profile = AssociateProfile.objects.select_related(
                "user"
            ).get(
                associate_id=associate_id,
            )
        except AssociateProfile.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid Associate ID or password."
            )

        user = authenticate(
            username=profile.user.username,
            password=password,
        )

        if user is None or not user.is_active:
            raise serializers.ValidationError(
                "Invalid Associate ID or password."
            )

        if not user.is_associate_user:
            raise serializers.ValidationError(
                "This account is not an associate account."
            )

        attrs["user"] = user
        attrs["profile"] = profile

        return attrs


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        username = attrs["username"].strip()
        password = attrs["password"]

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None or not user.is_active:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_admin_user:
            raise serializers.ValidationError(
                "Administrator access is required."
            )

        attrs["user"] = user

        return attrs


class AssociateProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociateProfile
        fields = [
            "name",
            "email",
            "phone",
            "picture",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(
            attrs["current_password"]
        ):
            raise serializers.ValidationError(
                {
                    "current_password": (
                        "Current password is incorrect."
                    )
                }
            )

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": (
                        "Passwords do not match."
                    )
                }
            )

        validate_password(
            attrs["new_password"],
            user=user,
        )

        return attrs


class AssociateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=150,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )

    picture = serializers.ImageField(
        required=False,
        allow_null=True,
    )

    def create(self, validated_data):
        profile, temporary_password = create_associate(
            **validated_data
        )

        self._temporary_password = temporary_password

        return profile

    def to_representation(self, instance):
        data = AssociateProfileSerializer(
            instance,
            context=self.context,
        ).data

        data["temporary_password"] = getattr(
            self,
            "_temporary_password",
            None,
        )

        return data




