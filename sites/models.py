from django.db import models


class Site(models.Model):
    city = models.ForeignKey(
        "cities.City",
        on_delete=models.PROTECT,
        related_name="sites",
    )

    title = models.CharField(
        max_length=200,
    )

    address = models.TextField()

    description = models.TextField(
        blank=True,
    )

    map_image = models.ImageField(
        upload_to="sites/maps/",
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
        return self.title

class SiteMedia(models.Model):
    IMAGE = "image"
    VIDEO = "video"

    MEDIA_TYPE_CHOICES = (
        (IMAGE, "Image"),
        (VIDEO, "Video"),
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="media",
    )

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
    )

    file = models.FileField(
        upload_to="sites/media/",
    )

    ordering = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["ordering", "id"]

    def __str__(self):
        return f"{self.site.title} - {self.media_type} - {self.id}"

class SiteFeature(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="features",
    )

    label = models.CharField(
        max_length=100,
    )

    value = models.TextField()

    ordering = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["ordering", "id"]

    def __str__(self):
        return f"{self.label}: {self.value}"