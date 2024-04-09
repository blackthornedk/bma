"""The Video model."""
from django.db import models
from files.models import BaseFile
from taggit.managers import TaggableManager
from utils.models import UUIDTaggedItem
from utils.upload import get_upload_path


class Video(BaseFile):  # type: ignore[django-manager-missing]
    """The Video model."""

    original = models.FileField(
        upload_to=get_upload_path,
        max_length=255,
        help_text="The original uploaded video file.",
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this video file",
    )
