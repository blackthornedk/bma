"""The filters used for album list endpoints."""
import uuid
from typing import ClassVar

import django_filters
from ninja import Field
from utils.filters import ListFilters

from .models import Album


class AlbumFilters(ListFilters):
    """The filters used for the album_list endpoint."""

    files: list[uuid.UUID] = Field(None, alias="files")


class AlbumFilter(django_filters.FilterSet):
    """The Album filter."""

    class Meta:
        """Set model and fields."""

        model = Album
        fields: ClassVar[dict[str, list[str]]] = {
            "files": ["exact"],
            "title": ["exact", "icontains"],
            "description": ["icontains"],
        }
