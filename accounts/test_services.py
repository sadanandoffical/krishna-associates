from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AssociateProfile
from .services import create_associate


User = get_user_model()


class AssociateCreationTests(TestCase):

    def test_associate_creation_generates_credentials(self):
        profile, temporary_password = create_associate(
            name="New Associate",
            email="new@example.com",
            phone="9876543210",
        )

        self.assertIsInstance(
            profile,
            AssociateProfile,
        )

        self.assertTrue(
            profile.associate_id.startswith("KA-")
        )

        self.assertTrue(
            temporary_password
        )

        self.assertTrue(
            profile.user.check_password(
                temporary_password
            )
        )

        # The password must not be stored as plaintext.
        self.assertNotEqual(
            profile.user.password,
            temporary_password,
        )

    def test_associate_user_is_not_admin(self):
        profile, _ = create_associate(
            name="Normal Associate",
        )

        self.assertFalse(
            profile.user.is_staff
        )

        self.assertFalse(
            profile.user.is_superuser
        )

        self.assertEqual(
            profile.user.role,
            User.ROLE_ASSOCIATE,
        )