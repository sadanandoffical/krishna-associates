from django.contrib.auth import login, logout
from django.contrib.auth import update_session_auth_hash

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssociateProfile
from .permissions import IsAdminUser, IsAssociateUser
from .serializers import (
    AdminLoginSerializer,
    AssociateCreateSerializer,
    AssociateLoginSerializer,
    AssociateProfileSerializer,
    AdminAssociateListSerializer,
    AssociateProfileUpdateSerializer,
    ChangePasswordSerializer,
)
from .services import reset_associate_password


class AssociateLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AssociateLoginSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        profile = serializer.validated_data["profile"]

        login(request, user)

        return Response(
            {
                "message": "Login successful.",
                "user": {
                    "role": "associate",
                    "associate_id": profile.associate_id,
                    "name": profile.name,
                },
            }
        )


class AdminLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        login(request, user)

        return Response(
            {
                "message": "Login successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": "admin",
                },
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        return Response(
            {
                "message": "Logout successful."
            }
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_admin_user:
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": "admin",
                }
            )

        if user.is_associate_user:
            profile = user.associate_profile

            return Response(
                {
                    "id": user.id,
                    "role": "associate",
                    "associate": AssociateProfileSerializer(
                        profile,
                        context={"request": request},
                    ).data,
                }
            )

        return Response(
            {
                "detail": "Unsupported account type."
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class AssociateProfileView(APIView):
    permission_classes = [IsAssociateUser]

    def get(self, request):
        profile = request.user.associate_profile

        return Response(
            AssociateProfileSerializer(
                profile,
                context={"request": request},
            ).data
        )

    def patch(self, request):
        profile = request.user.associate_profile

        serializer = AssociateProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            AssociateProfileSerializer(
                profile,
                context={"request": request},
            ).data
        )


class AssociateChangePasswordView(APIView):
    permission_classes = [IsAssociateUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        user.set_password(
            serializer.validated_data["new_password"]
        )
        user.save(
            update_fields=["password"]
        )

        update_session_auth_hash(
            request,
            user,
        )

        return Response(
            {
                "message": "Password changed successfully."
            }
        )


class AdminCreateAssociateView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        profiles = (
            AssociateProfile.objects
            .select_related("user")
            .order_by("-created_at")
        )

        return Response(
            AdminAssociateListSerializer(
                profiles,
                many=True,
                context={"request": request},
            ).data
        )

    def post(self, request):
        serializer = AssociateCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        profile = serializer.save()

        return Response(
            serializer.to_representation(profile),
            status=status.HTTP_201_CREATED,
        )

class AdminAssociateDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, associate_id):
        try:
            profile = (
                AssociateProfile.objects
                .select_related("user")
                .get(associate_id=associate_id)
            )
        except AssociateProfile.DoesNotExist:
            return Response(
                {
                    "detail": "Associate not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        data = AdminAssociateListSerializer(
            profile,
            context={"request": request},
        ).data

        return Response(data)

class AdminAssociateStatusView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, associate_id):
        try:
            profile = (
                AssociateProfile.objects
                .select_related("user")
                .get(associate_id=associate_id)
            )
        except AssociateProfile.DoesNotExist:
            return Response(
                {
                    "detail": "Associate not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if "is_active" not in request.data:
            return Response(
                {
                    "is_active": [
                        "This field is required."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_active = request.data["is_active"]

        if not isinstance(is_active, bool):
            return Response(
                {
                    "is_active": [
                        "Must be a boolean."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.user.is_active = is_active
        profile.user.save(
            update_fields=["is_active"]
        )

        return Response(
            AdminAssociateListSerializer(
                profile,
                context={"request": request},
            ).data
        )

class AdminAssociateResetPasswordView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, associate_id):
        try:
            profile = (
                AssociateProfile.objects
                .select_related("user")
                .get(associate_id=associate_id)
            )
        except AssociateProfile.DoesNotExist:
            return Response(
                {
                    "detail": "Associate not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        temporary_password = reset_associate_password(
            profile
        )

        return Response(
            {
                "associate_id": profile.associate_id,
                "temporary_password": temporary_password,
            }
        )