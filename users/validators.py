import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_avatar(file):
    """Server-side check of an uploaded avatar: extension and size."""
    extension = os.path.splitext(file.name)[1].lower().lstrip(".")
    allowed = settings.ALLOWED_AVATAR_EXTENSIONS
    if extension not in allowed:
        raise ValidationError(
            "Unsupported file type. Allowed types: %(allowed)s.",
            params={"allowed": ", ".join(allowed)},
        )

    try:
        size = file.size
    except OSError:
        # The stored file is missing on disk; there is nothing to measure.
        return

    if size > settings.AVATAR_MAX_SIZE:
        max_mb = settings.AVATAR_MAX_SIZE / (1024 * 1024)
        raise ValidationError(
            "The image is too large. Maximum size is %(max)s MB.",
            params={"max": f"{max_mb:g}"},
        )
