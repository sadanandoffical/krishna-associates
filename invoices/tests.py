from datetime import date
from decimal import Decimal
from rest_framework.test import APITestCase
from django.test import TestCase
from io import BytesIO

from pypdf import PdfReader

from .pdf import (
    InvoicePDFError,
    render_invoice_pdf,
)

from django.utils import timezone
from rest_framework import status
from accounts.models import AssociateProfile, User
from cities.models import City
from customers.models import Customer
from .models import Invoice
from .serializers import InvoiceSerializer
from zipfile import ZipFile

class InvoiceNumberingTests(TestCase):

    def create_invoice(self, **overrides):
        data = {
            "payee_name": "Test Customer",
            "payee_address": "Lucknow",
            "amount": Decimal("10000.00"),
            "invoice_date": date.today(),
            "status": Invoice.STATUS_DRAFT,
        }

        data.update(overrides)

        return Invoice.objects.create(**data)

    def test_invoice_number_is_generated_automatically(self):
        invoice = self.create_invoice()

        self.assertIsNotNone(
            invoice.invoice_number
        )

        self.assertEqual(
            invoice.invoice_number,
            f"KA-INV-{invoice.pk:06d}",
        )

    def test_invoice_number_is_unique(self):
        invoice1 = self.create_invoice()
        invoice2 = self.create_invoice()

        self.assertNotEqual(
            invoice1.invoice_number,
            invoice2.invoice_number,
        )

        self.assertEqual(
            invoice1.invoice_number,
            f"KA-INV-{invoice1.pk:06d}",
        )

        self.assertEqual(
            invoice2.invoice_number,
            f"KA-INV-{invoice2.pk:06d}",
        )

    def test_invoice_number_is_not_changed_on_update(self):
        invoice = self.create_invoice()

        original_number = invoice.invoice_number

        invoice.amount = Decimal("25000.00")
        invoice.save()

        invoice.refresh_from_db()

        self.assertEqual(
            invoice.invoice_number,
            original_number,
        )

    # def test_invoice_number_is_editable_false(self):
    #     field = Invoice._meta.get_field(
    #         "invoice_number"
    #     )

    #     self.assertFalse(
    #         field.editable
    #     )

    def test_invoice_number_has_expected_format(self):
        invoice = self.create_invoice()

        self.assertRegex(
            invoice.invoice_number,
            r"^KA-INV-\d{6}$",
        )

    def test_invoice_new_payment_fields_are_saved(self):
        invoice = Invoice.objects.create(
            payee_name="Test Customer",
            payee_address="Test Address",
            project="Shesh Vihar",
            plot_area=500,
            plot_rate=600,
            plot_cost=300000,
            paid_amount=5000,
            due_amount=260000,
            payment_type="EMI Payment",
            total_paid=40000,
            payment_mode="IMPS",
            transaction_id="538147412146",
            bank_name="ICICI Bank",
            amount=5000,
            invoice_date=date(2026, 8, 2),
            status=Invoice.STATUS_DRAFT,
        )

        invoice.refresh_from_db()

        self.assertEqual(invoice.project, "Shesh Vihar")
        self.assertEqual(invoice.plot_area, Decimal("500"))
        self.assertEqual(invoice.plot_rate, Decimal("600"))
        self.assertEqual(invoice.plot_cost, Decimal("300000"))
        self.assertEqual(invoice.paid_amount, Decimal("5000"))
        self.assertEqual(invoice.due_amount, Decimal("260000"))
        self.assertEqual(invoice.payment_type, "EMI Payment")
        self.assertEqual(invoice.total_paid, Decimal("40000"))
        self.assertEqual(invoice.payment_mode, "IMPS")
        self.assertEqual(invoice.transaction_id, "538147412146")
        self.assertEqual(invoice.bank_name, "ICICI Bank")

    def test_amount_in_words_is_generated_from_paid_amount(self):
        invoice = Invoice.objects.create(
            payee_name="Test Customer",
            payee_address="Test Address",
            paid_amount=5000,
            invoice_date=date(2026, 8, 2),
            status=Invoice.STATUS_DRAFT,
        )

        self.assertEqual(
            invoice.amount_in_words,
            "Five Thousand Only",
        )

    def test_amount_in_words_updates_when_paid_amount_changes(self):
        invoice = Invoice.objects.create(
            payee_name="Test Customer",
            payee_address="Test Address",
            paid_amount=5000,
            invoice_date=date(2026, 8, 2),
            status=Invoice.STATUS_DRAFT,
        )

        self.assertEqual(
            invoice.amount_in_words,
            "Five Thousand Only",
        )

        invoice.paid_amount = 7500
        invoice.save()

        invoice.refresh_from_db()

        self.assertEqual(
            invoice.amount_in_words,
            "Seven Thousand Five Hundred Only",
        )

    def test_amount_in_words_ignores_decimal_part(self):
        invoice = Invoice.objects.create(
            payee_name="Test Customer",
            payee_address="Test Address",
            paid_amount=5000.75,
            invoice_date=date(2026, 8, 2),
            status=Invoice.STATUS_DRAFT,
        )

        self.assertEqual(
            invoice.amount_in_words,
            "Five Thousand Only",
        )

    def test_amount_in_words_is_empty_when_paid_amount_is_null(self):
        invoice = Invoice.objects.create(
            payee_name="Test Customer",
            payee_address="Test Address",
            paid_amount=None,
            invoice_date=date(2026, 8, 2),
            status=Invoice.STATUS_DRAFT,
        )

        self.assertEqual(invoice.amount_in_words, "")



class InvoiceSerializerTests(TestCase):

    def setUp(self):
        self.city = City.objects.create(
            name="Lucknow"
        )

        self.customer = Customer.objects.create(
            name="Rahul Sharma",
            phone="9876543210",
            city=self.city,
            address="12 Gomti Nagar, Lucknow",
        )

    def valid_data(self):
        return {
            "payee_name": "Manual Payee",
            "payee_address": "Manual Address, Lucknow",
            "amount": "25000.00",
            "invoice_date": date.today(),
            "status": Invoice.STATUS_DRAFT,
        }

    def test_manual_invoice_is_valid(self):
        serializer = InvoiceSerializer(
            data=self.valid_data()
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_customer_invoice_is_valid(self):
        data = self.valid_data()
        data["customer"] = self.customer.id

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_customer_invoice_prefills_payee_details(self):
        data = self.valid_data()

        data["customer"] = self.customer.id

        data["payee_name"] = "Fake Name"
        data["payee_address"] = "Fake Address"

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["payee_name"],
            "Rahul Sharma",
        )

        self.assertEqual(
            serializer.validated_data["payee_address"],
            "12 Gomti Nagar, Lucknow",
        )

    def test_manual_invoice_requires_payee_name(self):
        data = self.valid_data()

        data["payee_name"] = ""

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "payee_name",
            serializer.errors,
        )

    def test_manual_invoice_requires_payee_address(self):
        data = self.valid_data()

        data["payee_address"] = ""

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "payee_address",
            serializer.errors,
        )

    def test_negative_amount_is_rejected(self):
        data = self.valid_data()

        data["amount"] = "-1.00"

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "amount",
            serializer.errors,
        )

    def test_zero_amount_is_allowed(self):
        data = self.valid_data()

        data["amount"] = "0.00"

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_customer_without_address_is_rejected(self):
        customer = Customer.objects.create(
            name="No Address Customer",
            phone="9000000000",
        )

        data = self.valid_data()
        data["customer"] = customer.id

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "customer",
            serializer.errors,
        )

    def test_invoice_number_is_not_writable(self):
        data = self.valid_data()

        data["invoice_number"] = "KA-INV-999999"

        serializer = InvoiceSerializer(
            data=data
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertNotIn(
            "invoice_number",
            serializer.validated_data,
        )

class InvoiceAPITests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="invoice_admin",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.associate_user = User.objects.create_user(
            username="invoice_associate",
            password="StrongPassword123!",
        )

        self.associate_profile = AssociateProfile.objects.create(
            user=self.associate_user,
            associate_id="KA-INVOICE01",
            name="Invoice Associate",
            phone="9876543210",
        )

        self.city = City.objects.create(
            name="Lucknow",
        )

        self.customer = Customer.objects.create(
            name="Invoice Customer",
            phone="9123456789",
            city=self.city,
            address="Gomti Nagar, Lucknow",
        )

    def invoice_payload(self):
        return {
            "customer": self.customer.id,
            "amount": "25000.00",
            "invoice_date": "2026-09-13",
            "status": Invoice.STATUS_DRAFT,
        }

    def manual_invoice_payload(self):
        return {
            "payee_name": "Manual Payee",
            "payee_address": "Hazratganj, Lucknow",
            "amount": "15000.00",
            "invoice_date": "2026-09-13",
            "status": Invoice.STATUS_DRAFT,
        }

    def test_anonymous_cannot_list_invoices(self):
        response = self.client.get(
            "/api/invoices/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_associate_cannot_list_invoices(self):
        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.get(
            "/api/invoices/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_admin_can_list_invoices(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/invoices/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_admin_can_create_customer_invoice(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/invoices/",
            self.invoice_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.content,
        )

        data = response.json()

        self.assertEqual(
            data["customer"],
            self.customer.id,
        )

        self.assertEqual(
            data["payee_name"],
            self.customer.name,
        )

        self.assertEqual(
            data["payee_address"],
            self.customer.address,
        )

        self.assertTrue(
            data["invoice_number"].startswith(
                "KA-INV-"
            )
        )

    def test_admin_can_create_manual_invoice(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            "/api/invoices/",
            self.manual_invoice_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.content,
        )

        data = response.json()

        self.assertIsNone(
            data["customer"]
        )

        self.assertEqual(
            data["payee_name"],
            "Manual Payee",
        )

    def test_client_cannot_set_invoice_number(self):
        self.client.force_authenticate(
            user=self.admin
        )

        payload = self.invoice_payload()

        payload["invoice_number"] = (
            "KA-INV-999999"
        )

        response = self.client.post(
            "/api/invoices/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertNotEqual(
            response.json()["invoice_number"],
            "KA-INV-999999",
        )

    def test_admin_can_retrieve_invoice(self):
        self.client.force_authenticate(
            user=self.admin
        )

        create_response = self.client.post(
            "/api/invoices/",
            self.invoice_payload(),
            format="json",
        )

        invoice_id = create_response.json()["id"]

        response = self.client.get(
            f"/api/invoices/{invoice_id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["id"],
            invoice_id,
        )

    def test_admin_can_update_invoice(self):
        self.client.force_authenticate(
            user=self.admin
        )

        create_response = self.client.post(
            "/api/invoices/",
            self.invoice_payload(),
            format="json",
        )

        invoice_id = create_response.json()["id"]
        invoice_number = create_response.json()[
            "invoice_number"
        ]

        response = self.client.patch(
            f"/api/invoices/{invoice_id}/",
            {
                "amount": "30000.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["amount"],
            "30000.00",
        )

        self.assertEqual(
            response.json()["invoice_number"],
            invoice_number,
        )

    def test_admin_can_delete_invoice(self):
        self.client.force_authenticate(
            user=self.admin
        )

        create_response = self.client.post(
            "/api/invoices/",
            self.manual_invoice_payload(),
            format="json",
        )

        invoice_id = create_response.json()["id"]

        response = self.client.delete(
            f"/api/invoices/{invoice_id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            Invoice.objects.filter(
                id=invoice_id
            ).exists()
        )

    def test_nonexistent_invoice_returns_404(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/invoices/999999/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_anonymous_cannot_download_invoice_pdf(self):
        invoice = Invoice.objects.create(
            **self.manual_invoice_payload()
        )

        response = self.client.get(
            f"/api/invoices/{invoice.id}/pdf/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )


    def test_associate_cannot_download_invoice_pdf(self):
        invoice = Invoice.objects.create(
            **self.manual_invoice_payload()
        )

        self.client.force_authenticate(
            user=self.associate_user
        )

        response = self.client.get(
            f"/api/invoices/{invoice.id}/pdf/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )


    def test_admin_can_download_single_invoice_pdf(self):
        invoice = Invoice.objects.create(
            **self.manual_invoice_payload()
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/invoices/{invoice.id}/pdf/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertEqual(
            response["Content-Disposition"],
            (
                f'attachment; '
                f'filename="{invoice.invoice_number}.pdf"'
            ),
        )

        self.assertTrue(
            response.content.startswith(b"%PDF")
        )


    def test_missing_invoice_returns_404_for_pdf(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/invoices/999999/pdf/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

class InvoiceFilteringTests(InvoiceAPITests):

    def setUp(self):
        super().setUp()

        self.url = "/api/invoices/"


        self.invoice_1 = Invoice.objects.create(
            customer=self.customer,
            amount="1000.00",
            status="draft",
            invoice_date=timezone.localdate(),
        )

        self.invoice_2 = Invoice.objects.create(
            customer=self.customer,
            amount="2000.00",
            status="issued",
            invoice_date=timezone.localdate(),
        )

        self.other_customer = Customer.objects.create(
            name="Other Customer",
            phone="9999999999",
            address="Other Address",
        )

        self.invoice_3 = Invoice.objects.create(
            customer=self.other_customer,
            amount="3000.00",
            status="paid",
            invoice_date=timezone.localdate(),
        )

    def test_search_by_invoice_number(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"{self.url}?search={self.invoice_1.invoice_number}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["invoice_number"],
            self.invoice_1.invoice_number,
        )

    def test_filter_by_customer(self):

        self.client.force_authenticate(
            user=self.admin
        )
        response = self.client.get(
            f"{self.url}?customer={self.other_customer.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            self.invoice_3.id,
        )

    def test_filter_by_status(self):

        self.client.force_authenticate(
            user=self.admin
        )
        response = self.client.get(
            f"{self.url}?status=paid"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            self.invoice_3.id,
        )

    def test_filter_by_created_at(self):
        self.client.force_authenticate(
            user=self.admin
        )

        created_date = self.invoice_1.created_at.date()

        response = self.client.get(
            f"{self.url}?created_at={created_date}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertGreaterEqual(len(results), 1)

        returned_ids = {
            item["id"]
            for item in results
        }

        self.assertIn(self.invoice_1.id, returned_ids)

    def test_filter_by_created_at_range(self):
        created_date = self.invoice_1.created_at.date()

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"{self.url}"
            f"?created_at_after={created_date}"
            f"&created_at_before={created_date}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertGreaterEqual(len(results), 1)

    def test_combined_filters(self):

        self.client.force_authenticate(
            user=self.admin
        )
        response = self.client.get(
            f"{self.url}"
            f"?customer={self.customer.id}"
            f"&status=issued"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            self.invoice_2.id,
        )

class CustomerInvoiceHistoryTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="history_admin",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.associate_user = User.objects.create_user(
            username="history_associate",
            password="StrongPassword123!",
        )

        self.city = City.objects.create(
            name="Lucknow",
        )

        self.customer = Customer.objects.create(
            name="History Customer",
            phone="9000000001",
            city=self.city,
            address="Gomti Nagar, Lucknow",
        )

        self.other_customer = Customer.objects.create(
            name="Other Customer",
            phone="9000000002",
            city=self.city,
            address="Hazratganj, Lucknow",
        )

        self.client.force_authenticate(
            user=self.admin,
        )

    def create_invoice(
        self,
        customer=None,
        amount="10000.00",
        invoice_date="2026-09-13",
    ):
        return Invoice.objects.create(
            customer=customer,
            payee_name=(
                customer.name
                if customer
                else "Manual Payee"
            ),
            payee_address=(
                customer.address
                if customer
                else "Manual Address"
            ),
            amount=amount,
            invoice_date=invoice_date,
            status=Invoice.STATUS_ISSUED,
        )

    def test_customer_invoice_history_returns_only_customer_invoices(self):
        first = self.create_invoice(
            customer=self.customer,
            amount="10000.00",
            invoice_date="2026-09-10",
        )

        second = self.create_invoice(
            customer=self.customer,
            amount="20000.00",
            invoice_date="2026-09-12",
        )

        self.create_invoice(
            customer=self.other_customer,
            amount="99999.00",
        )

        response = self.client.get(
            f"/api/invoices/customer/{self.customer.id}/"
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

        self.assertEqual(
            len(data["results"]),
            2,
        )

        returned_ids = [
            item["id"]
            for item in data["results"]
        ]

        self.assertIn(
            first.id,
            returned_ids,
        )

        self.assertIn(
            second.id,
            returned_ids,
        )

        self.assertNotIn(
            Invoice.objects.filter(
                customer=self.other_customer
            ).first().id,
            returned_ids,
        )

    def test_history_is_ordered_newest_first(self):
        older = self.create_invoice(
            customer=self.customer,
            amount="10000.00",
            invoice_date="2026-09-01",
        )

        newer = self.create_invoice(
            customer=self.customer,
            amount="20000.00",
            invoice_date="2026-09-12",
        )

        response = self.client.get(
            f"/api/invoices/customer/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        self.assertEqual(
            results[0]["id"],
            newer.id,
        )

        self.assertEqual(
            results[1]["id"],
            older.id,
        )

    def test_customer_with_no_invoices_returns_empty_results(self):
        response = self.client.get(
            f"/api/invoices/customer/{self.other_customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["results"],
            [],
        )

        self.assertEqual(
            data["count"],
            0,
        )

    def test_nonexistent_customer_returns_404(self):
        response = self.client.get(
            "/api/invoices/customer/999999/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_anonymous_cannot_access_history(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            f"/api/invoices/customer/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_associate_cannot_access_history(self):
        self.client.force_authenticate(
            user=self.associate_user,
        )

        response = self.client.get(
            f"/api/invoices/customer/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_history_is_paginated(self):
        for index in range(15):
            self.create_invoice(
                customer=self.customer,
                amount=str(
                    1000 + index
                ) + ".00",
            )

        response = self.client.get(
            f"/api/invoices/customer/{self.customer.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "count",
            data,
        )

        self.assertIn(
            "results",
            data,
        )

        self.assertEqual(
            data["count"],
            15,
        )

        self.assertLessEqual(
            len(data["results"]),
            12,
        )

class InvoiceFinalHardeningTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="invoice_hardening_admin",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.associate_user = User.objects.create_user(
            username="invoice_hardening_associate",
            password="StrongPassword123!",
        )

        self.city = City.objects.create(
            name="Lucknow",
        )

        self.customer = Customer.objects.create(
            name="Hardening Customer",
            phone="9111111111",
            city=self.city,
            address="Gomti Nagar, Lucknow",
        )

        self.client.force_authenticate(
            user=self.admin,
        )

    def create_invoice(self, **overrides):
        data = {
            "customer": self.customer,
            "payee_name": self.customer.name,
            "payee_address": self.customer.address,
            "amount": Decimal("10000.00"),
            "invoice_date": date.today(),
            "status": Invoice.STATUS_DRAFT,
        }

        data.update(overrides)

        return Invoice.objects.create(**data)

    def test_invoice_number_cannot_be_changed(self):
        invoice = self.create_invoice()

        original_number = invoice.invoice_number

        response = self.client.patch(
            f"/api/invoices/{invoice.id}/",
            {
                "invoice_number": "KA-INV-999999",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        invoice.refresh_from_db()

        self.assertEqual(
            invoice.invoice_number,
            original_number,
        )

    def test_negative_amount_is_rejected_by_api(self):
        response = self.client.post(
            "/api/invoices/",
            {
                "payee_name": "Manual Payee",
                "payee_address": "Lucknow",
                "amount": "-100.00",
                "invoice_date": date.today(),
                "status": Invoice.STATUS_DRAFT,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "amount",
            response.json(),
        )

    def test_invalid_status_is_rejected(self):
        response = self.client.post(
            "/api/invoices/",
            {
                "payee_name": "Manual Payee",
                "payee_address": "Lucknow",
                "amount": "1000.00",
                "invoice_date": date.today(),
                "status": "invalid_status",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "status",
            response.json(),
        )

    def test_customer_invoice_uses_current_customer_details(self):
        invoice = self.create_invoice()

        self.customer.name = "Updated Customer Name"
        self.customer.address = "Updated Address, Lucknow"
        self.customer.save()

        response = self.client.patch(
            f"/api/invoices/{invoice.id}/",
            {
                "amount": "20000.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["payee_name"],
            "Updated Customer Name",
        )

        self.assertEqual(
            response.json()["payee_address"],
            "Updated Address, Lucknow",
        )

    def test_customer_can_be_cleared_for_manual_invoice(self):
        invoice = self.create_invoice()

        response = self.client.patch(
            f"/api/invoices/{invoice.id}/",
            {
                "customer": None,
                "payee_name": "Manual Payee",
                "payee_address": "Manual Address, Lucknow",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        invoice.refresh_from_db()

        self.assertIsNone(
            invoice.customer,
        )

        self.assertEqual(
            invoice.payee_name,
            "Manual Payee",
        )

        self.assertEqual(
            invoice.payee_address,
            "Manual Address, Lucknow",
        )

    def test_customer_without_address_cannot_be_used(self):
        customer = Customer.objects.create(
            name="Missing Address Customer",
            phone="9222222222",
        )

        response = self.client.post(
            "/api/invoices/",
            {
                "customer": customer.id,
                "amount": "5000.00",
                "invoice_date": date.today(),
                "status": Invoice.STATUS_DRAFT,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "customer",
            response.json(),
        )

    def test_invoice_delete_does_not_delete_customer(self):
        invoice = self.create_invoice()

        customer_id = self.customer.id

        response = self.client.delete(
            f"/api/invoices/{invoice.id}/",
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertTrue(
            Customer.objects.filter(
                id=customer_id,
            ).exists(),
        )

    def test_invoice_list_is_paginated(self):
        for index in range(15):
            self.create_invoice(
                amount=Decimal(
                    1000 + index
                ),
            )

        response = self.client.get(
            "/api/invoices/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "count",
            data,
        )

        self.assertIn(
            "results",
            data,
        )

        self.assertEqual(
            data["count"],
            15,
        )

        self.assertLessEqual(
            len(data["results"]),
            12,
        )

    def test_invoice_page_size_cannot_exceed_global_limit(self):
        for index in range(15):
            self.create_invoice(
                amount=Decimal(
                    1000 + index
                ),
            )

        response = self.client.get(
            "/api/invoices/?page_size=999999",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertLessEqual(
            len(data["results"]),
            50,
        )

    def test_invoice_detail_is_not_public(self):
        invoice = self.create_invoice()

        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            f"/api/invoices/{invoice.id}/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_invoice_detail_is_not_available_to_associate(self):
        invoice = self.create_invoice()

        self.client.force_authenticate(
            user=self.associate_user,
        )

        response = self.client.get(
            f"/api/invoices/{invoice.id}/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

class InvoicePDFRendererTests(TestCase):

    def setUp(self):
        self.invoice = Invoice.objects.create(
            
            payee_name="PDF Test Customer",
            payee_address="Gomti Nagar, Lucknow",
            amount=Decimal("25000.00"),
            invoice_date=date(2026, 9, 13),
            status=Invoice.STATUS_ISSUED,
            project="Shesh Vihar",
            plot_area=500,
            plot_rate=600,
            plot_cost=300000,
            paid_amount=25000,
            due_amount=260000,
            payment_type="EMI Payment",
            total_paid=40000,
            payment_mode="IMPS",
            transaction_id="538147412146",
            bank_name="ICICI Bank",
        )

    def test_invoice_pdf_returns_bytes(self):
        pdf = render_invoice_pdf(
            self.invoice
        )

        self.assertIsInstance(
            pdf,
            bytes,
        )

        self.assertGreater(
            len(pdf),
            100,
        )

    def test_invoice_pdf_has_pdf_signature(self):
        pdf = render_invoice_pdf(
            self.invoice
        )

        self.assertTrue(
            pdf.startswith(b"%PDF"),
        )

    def test_invoice_pdf_is_readable(self):
        pdf = render_invoice_pdf(
            self.invoice
        )

        reader = PdfReader(
            BytesIO(pdf)
        )

        self.assertGreaterEqual(
            len(reader.pages),
            1,
        )

    def test_invoice_pdf_contains_invoice_data(self):
        pdf = render_invoice_pdf(
            self.invoice
        )

        reader = PdfReader(
            BytesIO(pdf)
        )

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        self.assertIn(
            self.invoice.invoice_number,
            text,
        )

        self.assertIn(
            "PDF Test Customer",
            text,
        )

        self.assertIn(
            "Gomti Nagar, Lucknow",
            text,
        )

        self.assertIn(
            "25,000",
            text,
        )

    def test_unsaved_invoice_is_rejected(self):
        invoice = Invoice(
            payee_name="Unsaved",
            payee_address="Lucknow",
            amount=Decimal("1000.00"),
            invoice_date=date.today(),
        )

        with self.assertRaises(
            InvoicePDFError
        ):
            render_invoice_pdf(
                invoice
            )

class InvoiceBulkPDFTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="bulk_pdf_admin",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.associate = User.objects.create_user(
            username="bulk_pdf_associate",
            password="StrongPassword123!",
        )

        self.client.force_authenticate(
            user=self.admin,
        )

    def create_invoice(self, index):
        return Invoice.objects.create(
            payee_name=f"Bulk Customer {index}",
            payee_address=f"Address {index}, Lucknow",
            amount=Decimal(
                f"{1000 + index}.00"
            ),
            invoice_date=date(2026, 9, 13),
            status=Invoice.STATUS_ISSUED,
        )

    def test_bulk_pdf_returns_zip(self):
        invoice1 = self.create_invoice(1)
        invoice2 = self.create_invoice(2)

        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": (
                    f"{invoice1.id},"
                    f"{invoice2.id}"
                )
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/zip",
        )

    def test_bulk_pdf_contains_one_pdf_per_invoice(self):
        invoice1 = self.create_invoice(1)
        invoice2 = self.create_invoice(2)
        invoice3 = self.create_invoice(3)

        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": (
                    f"{invoice1.id},"
                    f"{invoice2.id},"
                    f"{invoice3.id}"
                )
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        archive = ZipFile(
            BytesIO(response.content)
        )

        names = archive.namelist()

        self.assertEqual(
            len(names),
            3,
        )

        self.assertIn(
            f"{invoice1.invoice_number}.pdf",
            names,
        )

        self.assertIn(
            f"{invoice2.invoice_number}.pdf",
            names,
        )

        self.assertIn(
            f"{invoice3.invoice_number}.pdf",
            names,
        )

        for name in names:
            pdf = archive.read(name)

            self.assertTrue(
                pdf.startswith(b"%PDF"),
            )

    def test_duplicate_invoice_ids_are_deduplicated(self):
        invoice = self.create_invoice(1)

        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": (
                    f"{invoice.id},"
                    f"{invoice.id},"
                    f"{invoice.id}"
                )
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        archive = ZipFile(
            BytesIO(response.content)
        )

        self.assertEqual(
            archive.namelist(),
            [
                f"{invoice.invoice_number}.pdf"
            ],
        )

    def test_missing_ids_return_404(self):
        invoice = self.create_invoice(1)

        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": (
                    f"{invoice.id},"
                    "999999"
                )
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        data = response.json()

        self.assertIn(
            999999,
            data["missing_ids"],
        )

    def test_invalid_ids_return_400(self):
        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": "abc,xyz"
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        data = response.json()

        self.assertIn(
            "invalid_ids",
            data,
        )

    def test_empty_ids_return_400(self):
        response = self.client.get(
            "/api/invoices/bulk-pdf/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_anonymous_cannot_bulk_export(self):
        invoice = self.create_invoice(1)

        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": str(invoice.id)
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_associate_cannot_bulk_export(self):
        invoice = self.create_invoice(1)

        self.client.force_authenticate(
            user=self.associate,
        )

        response = self.client.get(
            "/api/invoices/bulk-pdf/",
            {
                "ids": str(invoice.id)
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    