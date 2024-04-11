"""API related utility functions."""
from typing import TypeAlias

from albums.models import Album
from django.db.models import QuerySet
from files.models import BaseFile

from .schema import ApiMessageSchema

# type aliases to make API return types more readable
FileApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | dict[str, BaseFile | QuerySet[BaseFile] | str]]
AlbumApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | dict[str, Album | QuerySet[Album] | str]]
