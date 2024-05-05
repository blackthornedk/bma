"""The custom User model used in the BMA project."""
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
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
        blank=True,
        help_text="The description field of the user profile on the BornHack website.",
    )

    @property
    def is_creator(self) -> bool:
        """Bool based on membership of settings.BMA_CREATOR_GROUP_NAME."""
        creator_group, created = Group.objects.get_or_create(name=settings.BMA_CREATOR_GROUP_NAME)
        return creator_group in self.groups.all()

    @property
    def is_moderator(self) -> bool:
        """Bool based on membership of settings.BMA_MODERATOR_GROUP_NAME."""
        moderator_group, created = Group.objects.get_or_create(name=settings.BMA_MODERATOR_GROUP_NAME)
        return moderator_group in self.groups.all()

    @property
    def is_curator(self) -> bool:
        """Bool based on membership of settings.BMA_CURATOR_GROUP_NAME."""
        curator_group, created = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
        return curator_group in self.groups.all()
