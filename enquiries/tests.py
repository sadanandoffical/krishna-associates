from unittest.mock import patch

from django.test import TestCase, override_settings

from rest_framework.test import APITestCase

from .models import Enquiry
from .services import EnquiryEmailError, send_enquiry_email


class EnquirySerializerTests(TestCase):

    def test_valid_enquiry(self):
        from .serializers import EnquirySerializer

        serializer = EnquirySerializer(
            data={
                "name": "Rahul Sharma",
                "phone": "9876543210",
                "requirement": "Looking for a residential plot.",
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_empty_name_rejected(self):
        from .serializers import EnquirySerializer

        serializer = EnquirySerializer(
            data={
                "name": "   ",
                "phone": "9876543210",
                "requirement": "Plot required.",
            }
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_empty_phone_rejected(self):
        from .serializers import EnquirySerializer

        serializer = EnquirySerializer(
            data={
                "name": "Rahul",
                "phone": "   ",
                "requirement": "Plot required.",
            }
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "phone",
            serializer.errors,
        )

    def test_empty_requirement_rejected(self):
        from .serializers import EnquirySerializer

        serializer = EnquirySerializer(
            data={
                "name": "Rahul",
                "phone": "9876543210",
                "requirement": "   ",
            }
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "requirement",
            serializer.errors,
        )


class EnquiryAPITests(APITestCase):

    @override_settings(
        ENQUIRY_ADMIN_EMAIL="admin@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    @patch(
        "enquiries.views.send_enquiry_email"
    )
    def test_public_user_can_submit_enquiry(
        self,
        mock_send,
    ):
        response = self.client.post(
            "/api/enquiries/",
            {
                "name": "Rahul Sharma",
                "phone": "9876543210",
                "requirement": "Residential plot required.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            Enquiry.objects.count(),
            1,
        )

        mock_send.assert_called_once()

    @patch(
        "enquiries.views.send_enquiry_email"
    )
    def test_enquiry_validation_error_does_not_create_record(
        self,
        mock_send,
    ):
        response = self.client.post(
            "/api/enquiries/",
            {
                "name": "",
                "phone": "9876543210",
                "requirement": "Plot required.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Enquiry.objects.count(),
            0,
        )

        mock_send.assert_not_called()

    @override_settings(
        ENQUIRY_ADMIN_EMAIL="admin@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    @patch(
        "enquiries.views.send_enquiry_email",
        side_effect=EnquiryEmailError(
            "SMTP failure"
        ),
    )
    def test_smtp_failure_returns_503_and_rolls_back(
        self,
        mock_send,
    ):
        response = self.client.post(
            "/api/enquiries/",
            {
                "name": "Rahul Sharma",
                "phone": "9876543210",
                "requirement": "Residential plot required.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            503,
        )

        self.assertEqual(
            Enquiry.objects.count(),
            0,
        )

        mock_send.assert_called_once()

    def test_empty_payload_is_rejected(self):
        response = self.client.post(
            "/api/enquiries/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Enquiry.objects.count(),
            0,
        )

class EnquiryEmailServiceTests(TestCase):

    @override_settings(
        ENQUIRY_ADMIN_EMAIL="admin@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    @patch(
        "enquiries.services.send_mail"
    )
    def test_email_service_sends_expected_email(
        self,
        mock_send_mail,
    ):
        enquiry = Enquiry.objects.create(
            name="Rahul Sharma",
            phone="9876543210",
            requirement="Residential plot required.",
        )

        send_enquiry_email(
            enquiry
        )

        mock_send_mail.assert_called_once()

        call = mock_send_mail.call_args

        self.assertEqual(
            call.kwargs["from_email"],
            "website@example.com",
        )

        self.assertEqual(
            call.kwargs["recipient_list"],
            ["admin@example.com"],
        )

        self.assertIn(
            "Rahul Sharma",
            call.kwargs["message"],
        )

        self.assertIn(
            "9876543210",
            call.kwargs["message"],
        )

    @override_settings(
        ENQUIRY_ADMIN_EMAIL="",
    )
    def test_missing_admin_email_raises_error(self):
        enquiry = Enquiry.objects.create(
            name="Rahul",
            phone="9876543210",
            requirement="Plot required.",
        )

        with self.assertRaises(
            EnquiryEmailError
        ):
            send_enquiry_email(
                enquiry
            )