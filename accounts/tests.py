from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase

from .models import AssociateProfile


User = get_user_model()


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPassword123!",
        )

        self.associate_user = User.objects.create_user(
            username="KA-TEST1234",
            password="AssociatePassword123!",
            role=User.ROLE_ASSOCIATE,
        )

        self.associate_profile = AssociateProfile.objects.create(
            user=self.associate_user,
            associate_id="KA-TEST1234",
            name="Test Associate",
            email="associate@example.com",
            phone="9876543210",
        )

    def test_admin_login(self):
        response = self.client.post(
            reverse("admin-login"),
            {
                "username": "admin",
                "password": "AdminPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["user"]["role"],
            "admin",
        )

    def test_associate_login(self):
        response = self.client.post(
            reverse("associate-login"),
            {
                "associate_id": "KA-TEST1234",
                "password": "AssociatePassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["user"]["role"],
            "associate",
        )

    def test_invalid_associate_login(self):
        response = self.client.post(
            reverse("associate-login"),
            {
                "associate_id": "KA-TEST1234",
                "password": "wrong-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_associate_can_view_own_profile(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.get(
            reverse("associate-profile")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["associate_id"],
            "KA-TEST1234",
        )

    def test_admin_cannot_use_associate_profile_endpoint(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            reverse("associate-profile")
        )

        self.assertEqual(response.status_code, 403)

    def test_associate_cannot_create_associate(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.post(
            reverse("admin-create-associate"),
            {
                "name": "Another Associate",
                "email": "another@example.com",
                "phone": "9999999999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_view_profile(self):
        response = self.client.get(
            reverse("associate-profile")
        )

        self.assertEqual(response.status_code, 403)

    def test_associate_password_change(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.post(
            reverse("associate-change-password"),
            {
                "current_password": "AssociatePassword123!",
                "new_password": "NewAssociatePassword123!",
                "confirm_password": "NewAssociatePassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.associate_user.refresh_from_db()

        self.assertTrue(
            self.associate_user.check_password(
                "NewAssociatePassword123!"
            )
        )

    def test_associate_cannot_change_password_without_current_password(
        self,
    ):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.post(
            reverse("associate-change-password"),
            {
                "current_password": "wrong-password",
                "new_password": "NewAssociatePassword123!",
                "confirm_password": "NewAssociatePassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_admin_create_associate_returns_temporary_password_once(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse("admin-create-associate"),
            {
                "name": "Created Associate",
                "email": "created@example.com",
                "phone": "9999999999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertIn(
            "associate_id",
            response.data,
        )

        self.assertIn(
            "temporary_password",
            response.data,
        )

        self.assertTrue(
            response.data["temporary_password"]
        )

        self.assertNotIn(
            "password",
            response.data,
        )

        self.assertNotIn(
            "password_hash",
            response.data,
        )

    def test_associate_responses_never_expose_password(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        profile_response = self.client.get(
            reverse("associate-profile")
        )

        self.assertEqual(
            profile_response.status_code,
            200,
        )

        self.assertNotIn(
            "password",
            profile_response.data,
        )

        self.assertNotIn(
            "temporary_password",
            profile_response.data,
        )

        current_user_response = self.client.get(
            reverse("current-user")
        )

        self.assertEqual(
            current_user_response.status_code,
            200,
        )

        self.assertNotIn(
            "password",
            str(current_user_response.data),
        )

        self.assertNotIn(
            "temporary_password",
            str(current_user_response.data),
        )

    def test_admin_can_list_associates(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            reverse("admin-create-associate")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        associate = response.data[0]

        self.assertEqual(
            associate["associate_id"],
            "KA-TEST1234",
        )

        self.assertEqual(
            associate["name"],
            "Test Associate",
        )

        self.assertTrue(
            associate["is_active"]
        )

        self.assertNotIn(
            "password",
            associate,
        )

        self.assertNotIn(
            "temporary_password",
            associate,
        )

    def test_admin_can_view_associate_detail(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            reverse(
                "admin-associate-detail",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["associate_id"],
            "KA-TEST1234",
        )

        self.assertEqual(
            response.data["name"],
            "Test Associate",
        )

        self.assertEqual(
            response.data["email"],
            "associate@example.com",
        )

        self.assertTrue(
            response.data["is_active"]
        )

        self.assertNotIn(
            "password",
            response.data,
        )

        self.assertNotIn(
            "temporary_password",
            response.data,
        )

    def test_associate_cannot_list_associates(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.get(
            reverse("admin-create-associate")
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_list_associates(self):
        response = self.client.get(
            reverse("admin-create-associate")
        )

        self.assertEqual(response.status_code, 403)


    def test_associate_cannot_view_associate_detail(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.get(
            reverse(
                "admin-associate-detail",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_admin_get_unknown_associate_returns_404(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            reverse(
                "admin-associate-detail",
                kwargs={
                    "associate_id": "KA-NOTFOUND",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_admin_can_deactivate_associate(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            reverse(
                "admin-associate-status",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.associate_user.refresh_from_db()

        self.assertFalse(
            self.associate_user.is_active
        )

        self.assertFalse(
            response.data["is_active"]
        )

    def test_admin_status_update_requires_boolean(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            reverse(
                "admin-associate-status",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            ),
            {
                "is_active": "false",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_associate_cannot_change_associate_status(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.patch(
            reverse(
                "admin-associate-status",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_admin_status_update_unknown_associate_returns_404(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            reverse(
                "admin-associate-status",
                kwargs={
                    "associate_id": "KA-NOTFOUND",
                },
            ),
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_admin_can_reset_associate_password(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse(
                "admin-associate-reset-password",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["associate_id"],
            "KA-TEST1234",
        )

        temporary_password = response.data[
            "temporary_password"
        ]

        self.assertTrue(
            temporary_password
        )

        self.associate_user.refresh_from_db()

        self.assertTrue(
            self.associate_user.check_password(
                temporary_password
            )
        )

        self.assertFalse(
            self.associate_user.check_password(
                "AssociatePassword123!"
            )
        )

    def test_reset_password_response_does_not_change_profile_exposure(self):
        self.client.force_authenticate(
            user=self.admin
        )

        self.client.post(
            reverse(
                "admin-associate-reset-password",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            ),
            format="json",
        )

        response = self.client.get(
            reverse(
                "admin-associate-detail",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "temporary_password",
            response.data,
        )

        self.assertNotIn(
            "password",
            response.data,
        )

    def test_associate_cannot_reset_associate_password(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.post(
            reverse(
                "admin-associate-reset-password",
                kwargs={
                    "associate_id": "KA-TEST1234",
                },
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )


    def test_admin_reset_password_unknown_associate_returns_404(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse(
                "admin-associate-reset-password",
                kwargs={
                    "associate_id": "KA-NOTFOUND",
                },
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )