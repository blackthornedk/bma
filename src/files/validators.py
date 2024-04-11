"""Field validators."""
from django.core.exceptions import ValidationError


def validate_thumbnail_url(value: str) -> None:
    """Make sure thumbnail URLs are local relative URLs under /static/images/ or /media/."""
    if not value.startswith("/static/images/") and not value.startswith("/media/"):
        raise ValidationError("non-local")


def validate_file_status(value: str) -> None:
    """Make sure the file status is valid."""
    from .models import StatusChoices

    if value not in StatusChoices.names:
        raise ValidationError("bad-status")
