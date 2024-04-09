"""The filters used for the album_list endpoint."""
import uuid

from ninja import Field
from utils.filters import ListFilters


class AlbumFilters(ListFilters):
    """The filters used for the album_list endpoint."""

    files: list[uuid.UUID] = Field(None, alias="files")
