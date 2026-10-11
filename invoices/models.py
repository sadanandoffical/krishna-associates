from decimal import Decimal
import uuid

from django.db import transaction
from django.db import models


def number_to_words(number):
    ones = [
        "",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
    ]

    teens = [
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]

    tens = [
        "",
        "",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety",
    ]

    def convert_under_thousand(n):
        words = []

        if n >= 100:
            words.append(ones[n // 100])
            words.append("Hundred")
            n %= 100

        if 10 <= n <= 19:
            words.append(teens[n - 10])
        elif n >= 20:
            words.append(tens[n // 10])
            if n % 10:
                words.append(ones[n % 10])
        elif n > 0:
            words.append(ones[n])

        return " ".join(words)

    number = int(number)

    if number == 0:
        return "Zero Only"

    parts = []

    crore = number // 10_000_000
    number %= 10_000_000

    lakh = number // 100_000
    number %= 100_000

    thousand = number // 1_000
    number %= 1_000

    if crore:
        parts.append(f"{convert_under_thousand(crore)} Crore")

    if lakh:
        parts.append(f"{convert_under_thousand(lakh)} Lakh")

    if thousand:
        parts.append(f"{convert_under_thousand(thousand)} Thousand")

    if number:
        parts.append(convert_under_thousand(number))

    return " ".join(parts) + " Only"


class Invoice(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ISSUED = "issued"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_ISSUED, "Issued"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="invoices",
        blank=True,
        null=True,
    )

    payee_name = models.CharField(
        max_length=150,
    )

    payee_address = models.TextField()

    project = models.CharField(
        max_length=150,
        blank=True,
    )

    plot_area = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    plot_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    plot_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    due_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    payment_type = models.CharField(
        max_length=100,
        blank=True,
    )

    total_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    payment_mode = models.CharField(
        max_length=50,
        blank=True,
    )

    transaction_id = models.CharField(
        max_length=150,
        blank=True,
    )

    bank_name = models.CharField(
        max_length=150,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    amount_in_words = models.TextField(
        blank=True,
    )

    invoice_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):

        if self.paid_amount is not None:
            self.amount_in_words = number_to_words(
                self.paid_amount
            )

        is_new = self.pk is None


        if is_new:
            # invoice_number is unique, but the final number depends on
            # the database-generated primary key. Use a temporary unique
            # value for the INSERT, then replace it with the final number.
            temporary_number = f"KA-TEMP-{uuid.uuid4().hex}"

            with transaction.atomic():
                self.invoice_number = temporary_number

                super().save(*args, **kwargs)

                self.invoice_number = f"KA-INV-{self.pk:06d}"

                type(self).objects.filter(
                    pk=self.pk
                ).update(
                    invoice_number=self.invoice_number
                )

            return

        super().save(*args, **kwargs)