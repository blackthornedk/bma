"""The custom User model used in the BMA project."""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):  # type: ignore[django-manager-missing]
    """The custom User model used in the BMA project."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_credit_name = models.CharField(
        max_length=100,
        default="Unnamed user",
        help_text="The public_credit_name field of the user profile on the BornHack website.",
    )
    description = models.TextField(
        help_text="The description field of the user profile on the BornHack website.",
    )
    is_bma_moderator = models.BooleanField(
        help_text="User can approve/unapprove files in BMA",
        default=False,
    )
    is_bma_creator = models.BooleanField(
        help_text="User can upload files to BMA",
        default=False,
    )
    is_bma_curator = models.BooleanField(
        help_text="User can create albums and tag files in BMA",
        default=False,
    )
