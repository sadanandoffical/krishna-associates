from django.db import models


class Enquiry(models.Model):
    name = models.CharField(
        max_length=150,
    )

    phone = models.CharField(
        max_length=30,
    )

    requirement = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.phone}"