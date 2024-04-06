from guardian.shortcuts import assign_perm, remove_perm
import uuid
from django.utils import timezone
from django.db.models.manager import BaseManager
from django.utils.html import mark_safe

from django.urls import reverse
from django.conf import settings
from django.db import models
from polymorphic.models import PolymorphicModel, PolymorphicManager
from polymorphic.managers import PolymorphicQuerySet

from .validators import validate_thumbnail_url
from users.sentinel import get_sentinel_user


class StatusChoices(models.TextChoices):
    """The possible status choices for a file."""

    PENDING_MODERATION = ("PENDING_MODERATION", "Pending Moderation")
    UNPUBLISHED = ("UNPUBLISHED", "Unpublished")
    PUBLISHED = ("PUBLISHED", "Published")
    PENDING_DELETION = ("PENDING_DELETION", "Pending Deletion")


license_urls = {
    "CC_ZERO_1_0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC_BY_4_0": "https://creativecommons.org/licenses/by/4.0/",
    "CC_BY_SA_4_0": "https://creativecommons.org/licenses/by-sa/4.0/",
}


class LicenseChoices(models.TextChoices):
    """The choices for license for uploaded files."""

    CC_ZERO_1_0 = ("CC_ZERO_1_0", "Creative Commons CC0 1.0 Universal")
    CC_BY_4_0 = ("CC_BY_4_0", "Creative Commons Attribution 4.0 International")
    CC_BY_SA_4_0 = (
        "CC_BY_SA_4_0",
        "Creative Commons Attribution-ShareAlike 4.0 International",
    )


class FileTypeChoices(models.TextChoices):
    """The filetype filter."""

    picture = ("picture", "Picture")
    video = ("video", "Video")
    audio = ("audio", "Audio")
    document = ("document", "Document")



class BaseFileQuerySet(PolymorphicQuerySet):
    """Custom queryset and manager for file operations."""
    def approve(self):
        """Approve files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.approve()
        return updated

    def unapprove(self):
        """Unapprove files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.unapprove()
        return updated

    def publish(self):
        """Publish files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.publish()
        return updated

    def unpublish(self):
        """Unpublish files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.unpublish()
        return updated


class BaseFile(PolymorphicModel):
    """The polymorphic base model inherited by the Picture, Video, Audio, and Document models."""

    class Meta:
        ordering = ["created"]
        permissions = (
            ("unapprove_basefile", "Unapprove file"),
            ("approve_basefile", "Approve file"),
            ("unpublish_basefile", "Unpublish file"),
            ("publish_basefile", "Publish file"),
        )

    objects = PolymorphicManager.from_queryset(BaseFileQuerySet)()

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET(get_sentinel_user),
        related_name="files",
        help_text="The uploader of this file.",
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
        help_text="The title of this work. Required. Defaults to the original uploaded filename.",
    )

    description = models.TextField(
        blank=True,
        help_text="The description of this work. Optional. Supports markdown.",
    )

    source = models.URLField(
        help_text="The URL to the original source of this work. Leave blank to consider the BMA URL the original source.",
        blank=True,
    )

    license = models.CharField(
        max_length=255,
        choices=LicenseChoices.choices,
        blank=False,
        help_text="The license for this file. The license can not be changed after the file is uploaded.",
    )

    attribution = models.CharField(
        max_length=255,
        help_text="The attribution text for this file. This is usually the real name or handle of the author(s) or licensor of the file.",
    )

    status = models.CharField(
        max_length=20,
        blank=False,
        choices=StatusChoices.choices,
        default="PENDING_MODERATION",
        help_text="The status of this file. Only published files are visible on the public website.",
    )

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename. This value is read-only.",
    )

    file_size = models.PositiveIntegerField(
        help_text="The size of the file in bytes. This value is read-only.",
    )

    thumbnail_url = models.CharField(
        max_length=255,
        validators=[validate_thumbnail_url],
        help_text="Relative URL to the image to use as thumbnail for this file. This must be a string beginning with /static/images/ or /media/",
    )

    @property
    def filetype(self):
        return self._meta.model_name

    @property
    def filetype_icon(self):
        return settings.FILETYPE_ICONS[self.filetype]

    @property
    def status_icon(self):
        return settings.FILESTATUS_ICONS[self.status]

    def get_absolute_url(self):
        return reverse("files:detail", kwargs={"pk": self.pk})

    def resolve_links(self, request=None):
        """Return a dict of links for various actions on this object. Only return actions the current user has permission to do."""
        links = {
            "self": reverse("api-v1-json:file_get", kwargs={"file_uuid": self.uuid}),
            "downloads": {
                "original": self.original.url,
            },
        }
        if request:
            if request.user.has_perm("approve_basefile", self):
                links["approve"] = reverse(
                    "api-v1-json:approve_file",
                    kwargs={"file_uuid": self.uuid},
                )
            if request.user.has_perm("unapprove_basefile", self):
                links["unapprove"] = reverse(
                    "api-v1-json:unapprove_file",
                    kwargs={"file_uuid": self.uuid},
                ),
            if request.user.has_perm("publish_basefile", self):
                links["publish"] = reverse(
                    "api-v1-json:publish_file",
                    kwargs={"file_uuid": self.uuid},
                ),
            if request.user.has_perm("unpublish_basefile", self):
                links["unpublish"] = reverse(
                    "api-v1-json:unpublish_file",
                    kwargs={"file_uuid": self.uuid},
                ),
        if self.filetype == "picture":
            try:
                links["downloads"].update(
                    {
                        "small_thumbnail": self.small_thumbnail.url,
                        "medium_thumbnail": self.medium_thumbnail.url,
                        "large_thumbnail": self.large_thumbnail.url,
                        "small": self.small.url,
                        "medium": self.medium.url,
                        "large": self.large.url,
                        "slideshow": self.slideshow.url,
                    },
                )
            except OSError:
                # maybe file is missing from disk
                pass
        return links

    def approve(self, check: bool = False):
        """Approve file (change status to UNPUBLISHED)."""
        updated = BaseFile.objects.filter(uuid=self.uuid).update(
            status="UNPUBLISHED",
            updated=timezone.now(),
        )
        if updated:
            print(f"approve() assigning permissions, updated is {updated}")
            assign_perm("publish_basefile", self.owner, self)
            assign_perm("unpublish_basefile", self.owner, self)
        return updated

    def unapprove(self, check: bool = False):
        """Unapprove file (change status to PENDING_MODERATION)."""
        updated = BaseFile.objects.filter(uuid=self.uuid).update(
            status="PENDING_MODERATION",
            updated=timezone.now(),
        )
        if updated:
            print(f"unapprove() assigning permissions, updated is {updated}")
            remove_perm("publish_basefile", self.owner, self)
            remove_perm("unpublish_basefile", self.owner, self)
        return updated
