from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.services import create_associate
from cities.models import City

from .models import Customer
from accounts.models import AssociateProfile
from invoices.models import Invoice


User = get_user_model()

def test_admin_can_change_customer_city_and_associate(self):
    another_city = City.objects.create(
        name="Kanpur",
    )

    another_associate_user, another_profile, _ = create_associate(
        name="Another Associate",
        email="another@example.com",
        phone="9123456789",
    )

    self.client.force_authenticate(
        user=self.admin
    )

    response = self.client.patch(
        f"/api/customers/{self.customer.id}/",
        {
            "city": another_city.id,
            "associate": another_profile.id,
        },
        format="json",
    )

    self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
    )

    self.customer.refresh_from_db()

    self.assertEqual(
        self.customer.city_id,
        another_city.id,
    )

    self.assertEqual(
        self.customer.associate_id,
        another_profile.id,
    )

def test_admin_can_clear_optional_customer_fields(self):
    self.client.force_authenticate(
        user=self.admin
    )

    response = self.client.patch(
        f"/api/customers/{self.customer.id}/",
        {
            "city": None,
            "associate": None,
            "emi_start_date": None,
        },
        format="json",
    )

    self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
    )

    self.customer.refresh_from_db()

    self.assertIsNone(
        self.customer.city
    )

    self.assertIsNone(
        self.customer.associate
    )

    self.assertIsNone(
        self.customer.emi_start_date
    )


class CustomerAPITests(APITestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow",
        )

        self.other_city = City.objects.create(
            name="Kanpur",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="AdminPass123!",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )

        associate_profile, _ = create_associate(
            name="Amit Kumar",
            email="amit@example.com",
            phone="9876543210",
        )
        associate_user = associate_profile.user
        self.associate = associate_user
        self.associate_profile = associate_profile

        self.customer = Customer.objects.create(
            name="Rahul Sharma",
            phone="9876543211",
            city=self.city,
            associate=self.associate_profile,
            emi_start_date="2026-10-01",
            address="Gomti Nagar, Lucknow",
        )

    # ---------------------------------------------------------
    # Permission tests
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_customers(self):
        response = self.client.get(
            "/api/customers/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_associate_cannot_list_customers(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.get(
            "/api/customers/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_associate_cannot_create_customer(self):
        self.client.force_authenticate(
            user=self.associate
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Unauthorized Customer",
                "phone": "9000000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ---------------------------------------------------------
    # Admin CRUD
    # ---------------------------------------------------------

    def test_admin_can_list_customers(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/customers/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_admin_can_retrieve_customer(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/customers/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["name"],
            "Rahul Sharma",
        )

        self.assertEqual(
            response.data["city_name"],
            "Lucknow",
        )

        self.assertEqual(
            response.data["associate_name"],
            "Amit Kumar",
        )

    def test_admin_can_create_customer(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Priya Sharma",
                "phone": "9000000001",
                "city": self.city.id,
                "associate": self.associate_profile.id,
                "emi_start_date": "2026-11-01",
                "address": "Indira Nagar, Lucknow",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Customer.objects.filter(
                name="Priya Sharma"
            ).exists()
        )

    def test_admin_can_create_customer_with_property_details(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Property Customer",
                "phone": "9000000010",
                "address": "Gomti Nagar, Lucknow",
                "project": "SHESH VIHAR",
                "plot_area": "500 sq. ft.",
                "plot_rate": "600.00",
                "plot_cost": "300000.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        customer = Customer.objects.get(
            name="Property Customer"
        )

        self.assertEqual(
            customer.project,
            "SHESH VIHAR",
        )

        self.assertEqual(
            customer.plot_area,
            "500 sq. ft.",
        )

        self.assertEqual(
            customer.plot_rate,
            600,
        )

        self.assertEqual(
            customer.plot_cost,
            300000,
        )

        self.assertEqual(
            response.data["project"],
            "SHESH VIHAR",
        )

        self.assertEqual(
            response.data["plot_area"],
            "500 sq. ft.",
        )

        self.assertEqual(
            response.data["plot_rate"],
            "600.00",
        )

        self.assertEqual(
            response.data["plot_cost"],
            "300000.00",
        )

    def test_admin_can_create_customer_without_city_or_associate(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Walk-in Customer",
                "phone": "9000000002",
                "address": "Lucknow",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        customer = Customer.objects.get(
            name="Walk-in Customer"
        )

        self.assertIsNone(
            customer.city
        )

        self.assertIsNone(
            customer.associate
        )

    def test_admin_can_update_customer(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.patch(
            f"/api/customers/{self.customer.id}/",
            {
                "name": "Rahul Kumar",
                "phone": "9999999999",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.customer.refresh_from_db()

        self.assertEqual(
            self.customer.name,
            "Rahul Kumar",
        )

        self.assertEqual(
            self.customer.phone,
            "9999999999",
        )

    def test_admin_can_delete_customer(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/customers/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Customer.objects.filter(
                id=self.customer.id
            ).exists()
        )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def test_search_by_name(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/customers/?search=Rahul"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_search_by_phone(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/customers/?search=9876543211"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_search_is_case_insensitive(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/customers/?search=rahul"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    # ---------------------------------------------------------
    # Filters
    # ---------------------------------------------------------

    def test_filter_by_city(self):
        other_customer = Customer.objects.create(
            name="Kanpur Customer",
            phone="9000000003",
            city=self.other_city,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/customers/?city={self.city.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_filter_by_associate(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/customers/?associate="
            f"{self.associate_profile.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_combined_search_and_filters(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/customers/"
            f"?search=Rahul"
            f"&city={self.city.id}"
            f"&associate={self.associate_profile.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_customer_name_cannot_be_empty(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "   ",
                "phone": "9000000004",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "name",
            response.data,
        )

    def test_customer_phone_cannot_be_empty(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Valid Customer",
                "phone": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "phone",
            response.data,
        )

    def test_invalid_city_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Invalid City Customer",
                "phone": "9000000005",
                "city": 999999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_associate_is_rejected(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Invalid Associate Customer",
                "phone": "9000000006",
                "associate": 999999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_nonexistent_customer_returns_404(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/customers/999999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

class CustomerDeletionProtectionTests(APITestCase):

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

        self.customer = Customer.objects.create(
            name="Rahul Sharma",
            phone="9876543210",
            city=self.city,
        )

    def test_customer_without_invoice_can_be_deleted(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/customers/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Customer.objects.filter(
                id=self.customer.id
            ).exists()
        )

    def test_customer_with_invoice_cannot_be_deleted(self):
        invoice = Invoice.objects.create(
            invoice_number="INV-TEST-001",
            customer=self.customer,
            payee_name=self.customer.name,
            payee_address=self.customer.address or "Lucknow",
            amount="10000.00",
            invoice_date="2026-09-13",
            status=Invoice.STATUS_DRAFT,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.delete(
            f"/api/customers/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "detail",
            response.data,
        )

        self.assertIn(
            "existing invoices",
            response.data["detail"],
        )

        self.assertTrue(
            Customer.objects.filter(
                id=self.customer.id
            ).exists()
        )

        self.assertTrue(
            Invoice.objects.filter(
                id=invoice.id
            ).exists()
        )


class CustomerDetailTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="customer_detail_admin",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.city = City.objects.create(
            name="Lucknow"
        )

        self.associate_user = User.objects.create_user(
            username="detail_associate",
            password="StrongPassword123!",
        )

        self.associate_profile = AssociateProfile.objects.create(
            user=self.associate_user,
            associate_id="KA-DETAIL01",
            name="Detail Associate",
            phone="9876543210",
        )

        self.customer = Customer.objects.create(
            name="Detail Customer",
            phone="9123456789",
            city=self.city,
            associate=self.associate_profile,
            address="Lucknow",
        )

        self.client.force_authenticate(
            user=self.admin
        )

    def test_customer_detail_returns_expected_fields(self):
        response = self.client.get(
            f"/api/customers/{self.customer.id}/"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["id"],
            self.customer.id,
        )

        self.assertEqual(
            data["name"],
            "Detail Customer",
        )

        self.assertEqual(
            data["phone"],
            "9123456789",
        )

        self.assertEqual(
            data["city"],
            self.city.id,
        )

        self.assertEqual(
            data["city_name"],
            "Lucknow",
        )

        self.assertEqual(
            data["associate"],
            self.associate_profile.id,
        )

        self.assertEqual(
            data["associate_name"],
            "Detail Associate",
        )

    def test_customer_detail_nonexistent_returns_404(self):
        response = self.client.get(
            "/api/customers/999999/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_customer_detail_does_not_expose_passwords(self):
        response = self.client.get(
            f"/api/customers/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertNotIn(
            "password",
            data,
        )

        self.assertNotIn(
            "password_hash",
            data,
        )

class CustomerEdgeCaseTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="customer_edge_admin",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.city = City.objects.create(
            name="Lucknow"
        )

        self.associate_user = User.objects.create_user(
            username="edge_associate",
            password="StrongPassword123!",
        )

        self.associate_profile = AssociateProfile.objects.create(
            user=self.associate_user,
            associate_id="KA-EDGE001",
            name="Edge Associate",
            phone="9876500000",
        )

        self.customer = Customer.objects.create(
            name="Edge Customer",
            phone="9123400000",
            city=self.city,
            associate=self.associate_profile,
            address="Lucknow",
        )

        self.client.force_authenticate(
            user=self.admin
        )

    def test_search_with_only_whitespace_returns_all_customers(self):
        response = self.client.get(
            "/api/customers/?search=%20%20%20"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertGreaterEqual(
            len(data["results"]),
            1,
        )

    def test_invalid_city_id_returns_empty_result(self):
        response = self.client.get(
            "/api/customers/?city=999999"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            len(data["results"]),
            0,
        )

    def test_invalid_associate_id_returns_empty_result(self):
        response = self.client.get(
            "/api/customers/?associate=999999"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            len(data["results"]),
            0,
        )

    def test_search_by_phone(self):
        response = self.client.get(
            "/api/customers/?search=912340000"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            len(data["results"]),
            1,
        )

        self.assertEqual(
            data["results"][0]["id"],
            self.customer.id,
        )

    def test_search_by_name_case_insensitive(self):
        response = self.client.get(
            "/api/customers/?search=edge%20customer"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            len(data["results"]),
            1,
        )

        self.assertEqual(
            data["results"][0]["id"],
            self.customer.id,
        )

    def test_customer_can_clear_optional_relationships(self):
        response = self.client.patch(
            f"/api/customers/{self.customer.id}/",
            {
                "city": None,
                "associate": None,
                "emi_start_date": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.customer.refresh_from_db()

        self.assertIsNone(
            self.customer.city
        )

        self.assertIsNone(
            self.customer.associate
        )

        self.assertIsNone(
            self.customer.emi_start_date
        )

    def test_customer_update_rejects_empty_name(self):
        response = self.client.patch(
            f"/api/customers/{self.customer.id}/",
            {
                "name": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_customer_update_rejects_empty_phone(self):
        response = self.client.patch(
            f"/api/customers/{self.customer.id}/",
            {
                "phone": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_pagination_page_size_is_capped(self):
        response = self.client.get(
            "/api/customers/?page_size=999999"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "results",
            data,
        )

        self.assertLessEqual(
            len(data["results"]),
            50,
        )

    def test_nonexistent_customer_update_returns_404(self):
        response = self.client.patch(
            "/api/customers/999999/",
            {
                "name": "Does Not Exist",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )