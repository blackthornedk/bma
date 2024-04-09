"""Schemas for album API calls."""
import uuid

from django.http import HttpRequest
from django.urls import reverse
from ninja import ModelSchema
from utils.schema import ApiResponseSchema

from albums.models import Album


class AlbumRequestSchema(ModelSchema):
    """Schema for Album create or update operations."""

    title: str = ""
    description: str = ""
    files: list[uuid.UUID]

    class Config:
        """Set model and fields."""

        model = Album
        model_fields = ("title", "description", "files")


"""Response schemas below here."""


class AlbumResponseSchema(ModelSchema):
    """Schema for outputting Albums in API operations."""

    links: dict[str, str | dict[str, str]]

    class Config:
        """Set model and fields."""

        model = Album
        model_fields = (
            "uuid",
            "owner",
            "created",
            "updated",
            "title",
            "description",
            "files",
        )

    @staticmethod
    def resolve_links(obj: Album, context: dict[str, HttpRequest]) -> dict[str, str | dict[str, str]]:
        """For now only a self link for albums."""
        return {
            "self": reverse("api-v1-json:album_get", kwargs={"album_uuid": obj.uuid}),
        }


class SingleAlbumResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single album object."""

    bma_response: AlbumResponseSchema


class MultipleAlbumResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple album objects."""

    bma_response: list[AlbumResponseSchema]
