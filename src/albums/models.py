"""The album model."""
import uuid

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models import F
from django.utils import timezone
from files.models import BaseFile
from psycopg2.extras import DateTimeTZRange
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

    deleted = models.BooleanField(
        default=False,
        help_text="Set true to mark album as deleted.",
    )

    class Meta:
        """Order by created date initially."""

        ordering = ("created",)

    def __str__(self) -> str:
        """The string representation of an album."""
        return f"{self.title} ({self.uuid})"

    def remove_members(self, file_uuids: list[str]) -> None:
        """End the memberships for the file_uuids."""
        for membership in self.memberships.filter(basefile__uuid__in=file_uuids):
            membership.period = DateTimeTZRange(membership.period.lower, timezone.now())
            membership.save(update_fields=["period"])


def from_now_to_forever() -> DateTimeTZRange:
    """Return a DateTimeTZRange starting now and never stopping."""
    return DateTimeTZRange(timezone.now(), None)


class AlbumMember(models.Model):
    """The through model linking Albums and files."""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    # if the basefile object gets deleted from database also delete the AlbumMember
    basefile = models.ForeignKey(BaseFile, related_name="memberships", on_delete=models.CASCADE)

    # if the album object gets deleted from database also delete the AlbumMembers
    album = models.ForeignKey(Album, related_name="memberships", on_delete=models.CASCADE)

    period = DateTimeRangeField(
        default=from_now_to_forever,
        help_text="The time range of this album membership. End time can be blank.",
    )

    class Meta:
        """Add ExclusionConstraints preventing overlaps and adjacent ranges with same availability."""

        constraints = (
            # we do not want overlapping memberships
            ExclusionConstraint(
                name="prevent_membership_overlaps",
                expressions=[
                    (F("basefile"), RangeOperators.EQUAL),
                    (F("album"), RangeOperators.EQUAL),
                    ("period", RangeOperators.OVERLAPS),
                ],
            ),
        )

    def __str__(self) -> str:
        """The string representation of an album member file."""
        return f"{self.basefile.uuid} is in album {self.album.uuid}"
