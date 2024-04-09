"""This module defines the base models used in the rest of the models."""
import uuid

from django.db import models
from taggit.models import GenericUUIDTaggedItemBase
from taggit.models import TaggedItemBase


class BaseModel(models.Model):
    """The BaseModel which all other models are based on."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        """This is an abstract class."""

        abstract = True


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    """Allows us to tag models with a UUID pk, use it with TaggableManager(through=UUIDTaggedItem)."""

    class Meta:
        """Pretty names."""

        verbose_name = "Tag"
        verbose_name_plural = "Tags"
