from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from customers.models import Customer

from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )

    customer_phone = serializers.CharField(
        source="customer.phone",
        read_only=True,
    )

    payee_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    payee_address = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    amount_in_words = serializers.CharField(
        read_only=True,
    )

    new_customer = serializers.JSONField(
        required=False,
        write_only=True,
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "customer",
            "customer_name",
            "customer_phone",
            "payee_name",
            "payee_address",
            "project",
            "plot_area",
            "plot_rate",
            "plot_cost",
            "paid_amount",
            "due_amount",
            "payment_type",
            "total_paid",
            "payment_mode",
            "transaction_id",
            "bank_name",
            "amount",
            "amount_in_words",
            "invoice_date",
            "status",
            "created_at",
            "updated_at",
            "new_customer",
        ]

        read_only_fields = [
            "id",
            "invoice_number",
            "customer_name",
            "customer_phone",
            "amount_in_words",
            "created_at",
            "updated_at",
        ]

    def validate_payee_name(self, value):
        value = value.strip()

        return value

    def validate_payee_address(self, value):
        value = value.strip()

        return value

    def validate_amount(self, value):
        if value < Decimal("0.00"):
            raise serializers.ValidationError(
                "Invoice amount cannot be negative."
            )

        return value

    def validate(self, attrs):
        new_customer = attrs.get("new_customer")

        if new_customer is not None:
            if self.instance is not None:
                raise serializers.ValidationError(
                    {
                        "new_customer": (
                            "A new customer can only be created "
                            "when creating an invoice."
                        )
                    }
                )

            if attrs.get("customer") is not None:
                raise serializers.ValidationError(
                    {
                        "customer": (
                            "Use either an existing customer or "
                            "new_customer, not both."
                        )
                    }
                )

            if not isinstance(new_customer, dict):
                raise serializers.ValidationError(
                    {
                        "new_customer": (
                            "New customer data must be an object."
                        )
                    }
                )

            name = str(
                new_customer.get("name", "")
            ).strip()

            phone = str(
                new_customer.get("phone", "")
            ).strip()

            address = str(
                new_customer.get("address", "")
            ).strip()

            errors = {}

            if not name:
                errors["name"] = (
                    "Customer name cannot be empty."
                )

            if not phone:
                errors["phone"] = (
                    "Customer phone cannot be empty."
                )

            if not address:
                errors["address"] = (
                    "Customer address cannot be empty."
                )

            if errors:
                raise serializers.ValidationError(
                    {
                        "new_customer": errors
                    }
                )

            new_customer["name"] = name
            new_customer["phone"] = phone
            new_customer["address"] = address

            return attrs

        customer = attrs.get(
            "customer",
            getattr(
                self.instance,
                "customer",
                None,
            ),
        )

        if customer is not None:
            customer_name = customer.name.strip()
            customer_address = (
                customer.address or ""
            ).strip()

            if not customer_name:
                raise serializers.ValidationError(
                    {
                        "customer": (
                            "The selected customer does not "
                            "have a valid name."
                        )
                    }
                )

            if not customer_address:
                raise serializers.ValidationError(
                    {
                        "customer": (
                            "The selected customer does not "
                            "have an address. Add the customer's "
                            "address before creating an invoice "
                            "for them."
                        )
                    }
                )

            attrs["payee_name"] = customer_name
            attrs["payee_address"] = customer_address

        else:
            payee_name = attrs.get(
                "payee_name",
                getattr(
                    self.instance,
                    "payee_name",
                    "",
                ),
            )

            payee_address = attrs.get(
                "payee_address",
                getattr(
                    self.instance,
                    "payee_address",
                    "",
                ),
            )

            payee_name = (
                payee_name or ""
            ).strip()

            payee_address = (
                payee_address or ""
            ).strip()

            if not payee_name:
                raise serializers.ValidationError(
                    {
                        "payee_name": (
                            "Payee name is required when "
                            "no customer is selected."
                        )
                    }
                )

            if not payee_address:
                raise serializers.ValidationError(
                    {
                        "payee_address": (
                            "Payee address is required when "
                            "no customer is selected."
                        )
                    }
                )

            attrs["payee_name"] = payee_name
            attrs["payee_address"] = payee_address

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        new_customer_data = validated_data.pop(
            "new_customer",
            None,
        )

        if new_customer_data is not None:
            customer = Customer.objects.create(
                name=new_customer_data["name"],
                phone=new_customer_data["phone"],
                address=new_customer_data["address"],
                project=new_customer_data.get("project", ""),
                plot_area=new_customer_data.get("plot_area", ""),
                plot_rate=new_customer_data.get("plot_rate") or None,
                plot_cost=new_customer_data.get("plot_cost") or None,
            )

            validated_data["customer"] = customer
            validated_data["payee_name"] = customer.name
            validated_data["payee_address"] = customer.address

            validated_data["project"] = customer.project
            validated_data["plot_area"] = customer.plot_area
            validated_data["plot_rate"] = customer.plot_rate
            validated_data["plot_cost"] = customer.plot_cost

        return Invoice.objects.create(
            **validated_data
        )


class CustomerInvoiceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "payee_name",
            "payee_address",
            "amount",
            "invoice_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields