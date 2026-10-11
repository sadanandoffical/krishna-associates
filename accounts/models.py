from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_ASSOCIATE = "associate"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_ASSOCIATE, "Associate"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_ASSOCIATE,
    )

    def save(self, *args, **kwargs):
        if self.is_superuser or self.is_staff:
            self.role = self.ROLE_ADMIN

        super().save(*args, **kwargs)

    @property
    def is_admin_user(self):
        return self.is_superuser or self.is_staff or self.role == self.ROLE_ADMIN

    @property
    def is_associate_user(self):
        return (
            self.is_active
            and not self.is_staff
            and not self.is_superuser
            and self.role == self.ROLE_ASSOCIATE
        )

    def __str__(self):
        return self.username


class AssociateProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="associate_profile",
    )

    associate_id = models.CharField(
        max_length=50,
        unique=True,
    )

    name = models.CharField(
        max_length=150,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    picture = models.ImageField(
        upload_to="associates/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.name} ({self.associate_id})"