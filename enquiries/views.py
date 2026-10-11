from django.db import transaction

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Enquiry
from .serializers import EnquirySerializer
from .services import (
    EnquiryEmailError,
    send_enquiry_email,
)


class EnquiryCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EnquirySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            with transaction.atomic():
                enquiry = Enquiry.objects.create(
                    **serializer.validated_data
                )

                send_enquiry_email(
                    enquiry
                )

        except EnquiryEmailError:
            return Response(
                {
                    "detail": (
                        "We could not submit your enquiry "
                        "right now. Please try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "detail": (
                    "Your enquiry has been submitted successfully."
                )
            },
            status=status.HTTP_201_CREATED,
        )