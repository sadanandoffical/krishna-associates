from django.conf import settings
from django.db import models


class Customer(models.Model):
    name = models.CharField(
        max_length=150,
    )

    phone = models.CharField(
        max_length=30,
    )

    city = models.ForeignKey(
        "cities.City",
        on_delete=models.PROTECT,
        related_name="customers",
        blank=True,
        null=True,
    )

    associate = models.ForeignKey(
        "accounts.AssociateProfile",
        on_delete=models.SET_NULL,
        related_name="customers",
        blank=True,
        null=True,
    )

    emi_start_date = models.DateField(
        blank=True,
        null=True,
    )

    address = models.TextField(
        blank=True,
    )

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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.phone}"