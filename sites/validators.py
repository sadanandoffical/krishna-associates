from pathlib import Path

from rest_framework import serializers
from PIL import Image
from .models import SiteMedia


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MAP_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mov",
}


def validate_map_image(uploaded_file):
    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    if extension not in MAP_IMAGE_EXTENSIONS:
        raise serializers.ValidationError(
            "Invalid map image format. "
            "Allowed formats: JPG, JPEG, PNG, WEBP."
        )

    max_size = 10 * 1024 * 1024  # 10 MB

    if uploaded_file.size > max_size:
        raise serializers.ValidationError(
            "Map image cannot exceed 10 MB."
        )

    try:
        image = Image.open(uploaded_file)
        image.verify()
    except Exception:
        raise serializers.ValidationError(
            "The uploaded file is not a valid image."
        )

    uploaded_file.seek(0)

    return uploaded_file

def validate_media_file(media_type, uploaded_file):
    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    if media_type == SiteMedia.IMAGE:
        if extension not in IMAGE_EXTENSIONS:
            raise serializers.ValidationError(
                "Invalid image format. "
                "Allowed formats: JPG, JPEG, PNG, WEBP."
            )

    elif media_type == SiteMedia.VIDEO:
        if extension not in VIDEO_EXTENSIONS:
            raise serializers.ValidationError(
                "Invalid video format. "
                "Allowed formats: MP4, WEBM, MOV."
            )

    else:
        raise serializers.ValidationError(
            "Invalid media type."
        )