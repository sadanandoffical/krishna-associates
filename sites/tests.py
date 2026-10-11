from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from accounts.services import create_associate
from cities.models import City
from .models import Site,SiteMedia,SiteFeature


User = get_user_model()


class SiteAPITests(APITestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="AdminPass123!",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )

        associate_profile, _ = create_associate(
            name="Test Associate",
            email="associate@example.com",
            phone="9876543210",
        )

        associate_user = associate_profile.user
        self.associate = associate_user
        self.associate_profile = associate_profile

        self.site = Site.objects.create(
            city=self.city,
            title="Krishna Enclave",
            address="Lucknow, Uttar Pradesh",
            description="Residential plotting project.",
        )

    # ---------------------------------------------------------
    # Public read access
    # ---------------------------------------------------------

    def test_anonymous_user_can_list_sites(self):
        response = self.client.get("/api/sites/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_anonymous_user_can_retrieve_site(self):
        response = self.client.get(
            f"/api/sites/{self.site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.site.id,
        )

        self.assertEqual(
            response.data["city_name"],
            "Lucknow",
        )

        self.assertEqual(
            response.data["media"],
            [],
        )

        self.assertEqual(
            response.data["features"],
            [],
        )

    # ---------------------------------------------------------
    # Associate read access
    # ---------------------------------------------------------

    def test_associate_can_list_sites(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.get("/api/sites/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_associate_can_retrieve_site(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.get(
            f"/api/sites/{self.site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    # ---------------------------------------------------------
    # Anonymous mutation protection
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_site(self):
        response = self.client.post(
            "/api/sites/",
            {
                "city": self.city.id,
                "title": "New Site",
                "address": "Lucknow",
                "description": "Test site",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_update_site(self):
        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "title": "Updated Site",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_delete_site(self):
        response = self.client.delete(
            f"/api/sites/{self.site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ---------------------------------------------------------
    # Associate mutation protection
    # ---------------------------------------------------------

    def test_associate_cannot_create_site(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.post(
            "/api/sites/",
            {
                "city": self.city.id,
                "title": "Associate Site",
                "address": "Lucknow",
                "description": "Should fail",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_associate_cannot_update_site(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "title": "Unauthorized Update",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_associate_cannot_delete_site(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.delete(
            f"/api/sites/{self.site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ---------------------------------------------------------
    # Admin CRUD
    # ---------------------------------------------------------

    def test_admin_can_create_site(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/sites/",
            {
                "city": self.city.id,
                "title": "New Krishna Project",
                "address": "Gomti Nagar, Lucknow",
                "description": "New residential project.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Site.objects.filter(
                title="New Krishna Project"
            ).exists()
        )

    def test_admin_can_update_site(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "title": "Updated Krishna Enclave",
                "description": "Updated description.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.site.refresh_from_db()

        self.assertEqual(
            self.site.title,
            "Updated Krishna Enclave",
        )

        self.assertEqual(
            self.site.description,
            "Updated description.",
        )

    def test_admin_can_delete_site(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/sites/{self.site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Site.objects.filter(
                id=self.site.id
            ).exists()
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_site_title_cannot_be_empty(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/sites/",
            {
                "city": self.city.id,
                "title": "   ",
                "address": "Lucknow",
                "description": "Test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "title",
            response.data,
        )

    def test_site_address_cannot_be_empty(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/sites/",
            {
                "city": self.city.id,
                "title": "Valid Site",
                "address": "   ",
                "description": "Test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "address",
            response.data,
        )

    def test_site_requires_city(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/sites/",
            {
                "title": "Site Without City",
                "address": "Lucknow",
                "description": "Test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "city",
            response.data,
        )

    def test_site_rejects_invalid_city(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/sites/",
            {
                "city": 999999,
                "title": "Invalid City Site",
                "address": "Lucknow",
                "description": "Test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "city",
            response.data,
        )

    # ---------------------------------------------------------
    # City relationship
    # ---------------------------------------------------------

    def test_site_can_be_moved_to_another_city(self):
        another_city = City.objects.create(
            name="Kanpur",
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "city": another_city.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.site.refresh_from_db()

        self.assertEqual(
            self.site.city_id,
            another_city.id,
        )

class SiteFeatureAPITests(APITestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="AdminPass123!",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )

        associate_profile, _ = create_associate(
            name="Test Associate",
            email="associate@example.com",
            phone="9876543210",
        )

        associate_user = associate_profile.user
        self.associate = associate_user

        self.site = Site.objects.create(
            city=self.city,
            title="Krishna Enclave",
            address="Lucknow, Uttar Pradesh",
            description="Residential project.",
        )

    def test_public_user_can_list_features(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            f"/api/sites/{self.site.id}/features/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_admin_can_create_feature(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/features/",
            {
                "label": "Plot Size",
                "value": "1000 sq.ft.",
                "ordering": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["label"],
            "Plot Size",
        )

        self.assertEqual(
            response.data["value"],
            "1000 sq.ft.",
        )

        self.assertEqual(
            self.site.features.count(),
            1,
        )

    def test_associate_cannot_create_feature(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/features/",
            {
                "label": "Plot Size",
                "value": "1000 sq.ft.",
                "ordering": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_create_feature(self):
        response = self.client.post(
            f"/api/sites/{self.site.id}/features/",
            {
                "label": "Plot Size",
                "value": "1000 sq.ft.",
                "ordering": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_update_feature(self):
        feature = self.site.features.create(
            label="Plot Size",
            value="1000 sq.ft.",
            ordering=1,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/features/{feature.id}/",
            {
                "value": "1200 sq.ft.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        feature.refresh_from_db()

        self.assertEqual(
            feature.value,
            "1200 sq.ft.",
        )

    def test_admin_can_delete_feature(self):
        feature = self.site.features.create(
            label="Plot Size",
            value="1000 sq.ft.",
            ordering=1,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/sites/{self.site.id}/features/{feature.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            self.site.features.filter(
                id=feature.id
            ).exists()
        )

    def test_feature_cannot_have_empty_label(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/features/",
            {
                "label": "   ",
                "value": "1000 sq.ft.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "label",
            response.data,
        )

    def test_feature_cannot_have_empty_value(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/features/",
            {
                "label": "Plot Size",
                "value": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "value",
            response.data,
        )

    def test_feature_cannot_be_accessed_through_wrong_site(self):
        another_site = Site.objects.create(
            city=self.city,
            title="Another Site",
            address="Lucknow",
            description="Another project.",
        )

        feature = another_site.features.create(
            label="Plot Size",
            value="1000 sq.ft.",
            ordering=1,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/sites/{self.site.id}/features/{feature.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_nonexistent_site_returns_404_for_feature_create(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/sites/999999/features/",
            {
                "label": "Plot Size",
                "value": "1000 sq.ft.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

class SiteMediaAPITests(APITestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="AdminPass123!",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )

        associate_profile, _ = create_associate(
            name="Test Associate",
            email="associate@example.com",
            phone="9876543210",
        )

        associate_user = associate_profile.user
        self.associate = associate_user

        self.site = Site.objects.create(
            city=self.city,
            title="Krishna Enclave",
            address="Lucknow, Uttar Pradesh",
            description="Residential project.",
        )

    def create_test_image(self):
        image = Image.new(
            "RGB",
            (100, 100),
            "white",
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
        )

        buffer.seek(0)

        return SimpleUploadedFile(
            "test.jpg",
            buffer.read(),
            content_type="image/jpeg",
        )

    def test_public_user_can_list_media(self):
        response = self.client.get(
            f"/api/sites/{self.site.id}/media/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_admin_can_upload_image(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/media/",
            {
                "media_type": "image",
                "file": self.create_test_image(),
                "ordering": 0,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            self.site.media.count(),
            1,
        )

        media = self.site.media.first()

        self.assertEqual(
            media.media_type,
            SiteMedia.IMAGE,
        )

    def test_associate_cannot_upload_media(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/media/",
            {
                "media_type": "image",
                "file": self.create_test_image(),
                "ordering": 0,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_upload_media(self):
        response = self.client.post(
            f"/api/sites/{self.site.id}/media/",
            {
                "media_type": "image",
                "file": self.create_test_image(),
                "ordering": 0,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_invalid_image_extension_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        fake_file = SimpleUploadedFile(
            "malware.exe",
            b"not an image",
            content_type="application/octet-stream",
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/media/",
            {
                "media_type": "image",
                "file": fake_file,
                "ordering": 0,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_negative_ordering_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/sites/{self.site.id}/media/",
            {
                "media_type": "image",
                "file": self.create_test_image(),
                "ordering": -1,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_media_cannot_be_accessed_through_wrong_site(self):
        another_site = Site.objects.create(
            city=self.city,
            title="Another Site",
            address="Lucknow",
        )

        media = another_site.media.create(
            media_type=SiteMedia.IMAGE,
            file=self.create_test_image(),
            ordering=0,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/sites/{self.site.id}/media/{media.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_admin_can_delete_media(self):
        media = self.site.media.create(
            media_type=SiteMedia.IMAGE,
            file=self.create_test_image(),
            ordering=0,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/sites/{self.site.id}/media/{media.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            self.site.media.filter(
                id=media.id
            ).exists()
        )

class SiteMapImageAPITests(APITestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="AdminPass123!",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )

        associate_profile, _ = create_associate(
            name="Test Associate",
            email="associate@example.com",
            phone="9876543210",
        )

        associate_user = associate_profile.user
        self.associate = associate_user

        self.site = Site.objects.create(
            city=self.city,
            title="Krishna Enclave",
            address="Lucknow, Uttar Pradesh",
            description="Residential project.",
        )

    def create_test_map(self):
        image = Image.new(
            "RGB",
            (500, 500),
            "white",
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
        )

        buffer.seek(0)

        return SimpleUploadedFile(
            "map.jpg",
            buffer.read(),
            content_type="image/jpeg",
        )

    def test_admin_can_upload_map_image(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "map_image": self.create_test_map(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.site.refresh_from_db()

        self.assertTrue(
            bool(self.site.map_image)
        )

    def test_associate_cannot_upload_map_image(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "map_image": self.create_test_map(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_upload_map_image(self):
        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "map_image": self.create_test_map(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_invalid_map_extension_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        invalid_file = SimpleUploadedFile(
            "map.exe",
            b"not an image",
            content_type="application/octet-stream",
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "map_image": invalid_file,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "map_image",
            response.data,
        )

    def test_fake_image_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        fake_image = SimpleUploadedFile(
            "fake.jpg",
            b"this is not actually an image",
            content_type="image/jpeg",
        )

        response = self.client.patch(
            f"/api/sites/{self.site.id}/",
            {
                "map_image": fake_image,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "map_image",
            response.data,
        )

class SiteHardeningAPITests(APITestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="AdminPass123!",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )

    def create_site(self, title):
        return Site.objects.create(
            city=self.city,
            title=title,
            address="Lucknow, Uttar Pradesh",
            description="Residential project.",
        )

    def test_site_list_is_paginated(self):
        for index in range(15):
            self.create_site(
                f"Site {index}"
            )

        response = self.client.get(
            "/api/sites/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "count",
            response.data,
        )

        self.assertIn(
            "results",
            response.data,
        )

        self.assertEqual(
            response.data["count"],
            15,
        )

        self.assertLessEqual(
            len(response.data["results"]),
            12,
        )

    def test_site_page_size_can_be_reduced(self):
        for index in range(10):
            self.create_site(
                f"Site {index}"
            )

        response = self.client.get(
            "/api/sites/?page_size=5"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertLessEqual(
            len(response.data["results"]),
            5,
        )

    def test_site_page_size_has_maximum(self):
        for index in range(60):
            self.create_site(
                f"Site {index}"
            )

        response = self.client.get(
            "/api/sites/?page_size=500"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertLessEqual(
            len(response.data["results"]),
            50,
        )

    def test_nonexistent_site_returns_404(self):
        response = self.client.get(
            "/api/sites/999999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_nonexistent_site_cannot_be_updated(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            "/api/sites/999999/",
            {
                "title": "Updated",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_nonexistent_site_cannot_be_deleted(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            "/api/sites/999999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_site_detail_contains_media_and_features(self):
        site = self.create_site(
            "Complete Site"
        )

        site.features.create(
            label="Plot Size",
            value="1000 sq.ft.",
            ordering=1,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/sites/{site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "media",
            response.data,
        )

        self.assertIn(
            "features",
            response.data,
        )

        self.assertEqual(
            len(response.data["features"]),
            1,
        )

    def test_deleting_site_cascades_features(self):
        site = self.create_site(
            "Delete Test Site"
        )

        feature = site.features.create(
            label="Plot Size",
            value="1000 sq.ft.",
            ordering=1,
        )

        feature_id = feature.id

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/sites/{site.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            SiteFeature.objects.filter(
                id=feature_id
            ).exists()
        )