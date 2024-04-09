"""The album model."""
import uuid

from django.db import models
from files.models import BaseFile
from taggit.managers import TaggableManager
from users.sentinel import get_sentinel_user
from utils.models import UUIDTaggedItem


class Album(models.Model):
    """The Album model is used to group files (from all users, like a spotify playlist)."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET(get_sentinel_user),
        related_name="albums",
        help_text="The creator of this album.",
    )

    created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this object was first created.",
    )

    updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this object was last updated.",
    )

    title = models.CharField(
        max_length=255,
        blank=False,
        help_text="The title of this album. Required.",
    )

    description = models.TextField(
        blank=True,
        help_text="The description of this album. Optional. Supports markdown.",
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this album.",
    )

    files = models.ManyToManyField(
        BaseFile,
        through="AlbumMember",
        related_name="albums",
    )

    class Meta:
        """Order by created date initially."""

        ordering = ("created",)

    def __str__(self) -> str:
        """The string representation of an album."""
        return f"{self.title} ({self.uuid})"


class AlbumMember(models.Model):
    """The through model linking Albums and files."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )
    basefile = models.ForeignKey(BaseFile, on_delete=models.CASCADE)

    album = models.ForeignKey(Album, on_delete=models.CASCADE)

    created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this file was first added to the album.",
    )

    updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this object was last updated.",
    )

    def __str__(self) -> str:
        """The string representation of an album member file."""
        return f"{self.basefile.uuid} is in album {self.album.uuid}"
