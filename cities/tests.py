from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import City


User = get_user_model()


class CityAPITests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="cityadmin",
            email="admin@example.com",
            password="AdminPassword123!",
        )

        self.associate = User.objects.create_user(
            username="KA-TEST0001",
            password="AssociatePassword123!",
            role=User.ROLE_ASSOCIATE,
        )

        self.city = City.objects.create(
            name="Lucknow",
        )

    def test_public_can_list_cities(self):
        response = self.client.get(
            reverse("city-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["name"],
            "Lucknow",
        )

    def test_public_can_view_city(self):
        response = self.client.get(
            reverse(
                "city-detail",
                kwargs={"pk": self.city.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["name"],
            "Lucknow",
        )

    def test_unauthenticated_user_cannot_create_city(self):
        response = self.client.post(
            reverse("city-list"),
            {
                "name": "Kanpur",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_associate_cannot_create_city(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.post(
            reverse("city-list"),
            {
                "name": "Kanpur",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_create_city(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse("city-list"),
            {
                "name": "Kanpur",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            City.objects.filter(
                name="Kanpur"
            ).exists()
        )

    def test_admin_can_update_city(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            reverse(
                "city-detail",
                kwargs={"pk": self.city.pk},
            ),
            {
                "name": "Lucknow City",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.city.refresh_from_db()

        self.assertEqual(
            self.city.name,
            "Lucknow City",
        )

    def test_associate_cannot_update_city(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.patch(
            reverse(
                "city-detail",
                kwargs={"pk": self.city.pk},
            ),
            {
                "name": "Changed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_delete_city_without_dependencies(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            reverse(
                "city-detail",
                kwargs={"pk": self.city.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            City.objects.filter(
                pk=self.city.pk
            ).exists()
        )

    def test_duplicate_city_name_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse("city-list"),
            {
                "name": "Lucknow",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_empty_city_name_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse("city-list"),
            {
                "name": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

class CityDeletionProtectionTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="deleteadmin",
            password="AdminPassword123!",
        )

        self.city = City.objects.create(
            name="Protected City",
        )

    def test_city_can_be_deleted_when_unused(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            reverse(
                "city-detail",
                kwargs={"pk": self.city.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )