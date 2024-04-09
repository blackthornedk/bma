"""API schemas for the BaseFile model."""
import uuid
from pathlib import Path

from django.http import HttpRequest
from ninja import ModelSchema
from ninja import Schema
from utils.permissions import get_object_permissions_schema
from utils.schema import ApiResponseSchema
from utils.schema import ObjectPermissionSchema

from files.models import BaseFile
from files.models import StatusChoices

from .models import LicenseChoices
from .models import license_urls


class UploadRequestSchema(ModelSchema):
    """Schema for file metatata for file upload requests."""

    license: LicenseChoices
    title: str = ""
    description: str = ""
    source: str = ""
    thumbnail_url: str = ""

    class Config:
        """Specify the model fields to allow."""

        model = BaseFile
        model_fields = (
            "license",
            "attribution",
            "title",
            "description",
            "source",
            "thumbnail_url",
        )


class FileUpdateRequestSchema(ModelSchema):
    """Schema for requests updating file metadata, all fields optional."""

    title: str | None = ""
    description: str | None = ""
    source: str | None = ""
    attribution: str | None = ""
    thumbnail_url: str | None = ""

    class Config:
        """Specify the model fields to allow."""

        model = BaseFile
        model_fields = (
            "title",
            "description",
            "source",
            "attribution",
            "thumbnail_url",
        )


class SingleFileRequestSchema(Schema):
    """The schema used for requests involving a single file."""

    file_uuid: uuid.UUID


class MultipleFileRequestSchema(Schema):
    """The schema used for requests involving multiple files."""

    file_uuids: list[uuid.UUID]


"""Response schemas below here."""


class FileResponseSchema(ModelSchema):
    """Schema used for responses including metadata of a file."""

    albums: list[uuid.UUID]
    filename: str
    links: dict[str, str | dict[str, str]]
    filetype: str
    filetype_icon: str
    status: str
    status_icon: str
    size_bytes: int
    permissions: ObjectPermissionSchema
    license_name: str
    license_url: str

    class Config:
        """Specify the model fields to include."""

        model = BaseFile
        model_fields = (
            "uuid",
            "owner",
            "created",
            "updated",
            "title",
            "description",
            "license",
            "attribution",
            "status",
            "source",
            "original_filename",
            "thumbnail_url",
        )

    @staticmethod
    def resolve_albums(obj: BaseFile, context: dict[str, HttpRequest]) -> list[str]:
        """Get the value for the albums field."""
        return [str(x) for x in obj.albums.values_list("uuid", flat=True)]

    @staticmethod
    def resolve_filename(obj: BaseFile, context: dict[str, HttpRequest]) -> str:
        """Get the value for the filename field."""
        return Path(obj.original.path).name

    @staticmethod
    def resolve_size_bytes(obj: BaseFile, context: dict[str, HttpRequest]) -> int:
        """Get the value for the size_bytes field, return 0 if file is not found."""
        if Path.exists(obj.original.path):
            return int(obj.original.size)
        return 0

    @staticmethod
    def resolve_links(obj: BaseFile, context: dict[str, HttpRequest]) -> dict[str, str | dict[str, str]]:
        """Get the value for the links field."""
        return obj.resolve_links(request=context["request"])

    @staticmethod
    def resolve_status(obj: BaseFile, context: dict[str, HttpRequest]) -> str:
        """Get the value for the file status field."""
        return StatusChoices[obj.status].label

    @staticmethod
    def resolve_permissions(obj: BaseFile, context: dict[str, HttpRequest]) -> ObjectPermissionSchema:
        """Get the value for the permissions field with all file permissions."""
        return get_object_permissions_schema(obj, context["request"])

    @staticmethod
    def resolve_license_name(obj: BaseFile, context: dict[str, HttpRequest]) -> str:
        """Get the value for the license_name field."""
        return str(getattr(LicenseChoices, obj.license).label)

    @staticmethod
    def resolve_license_url(obj: BaseFile, context: dict[str, HttpRequest]) -> str:
        """Get the value for the license_url field."""
        return license_urls[obj.license]

    @staticmethod
    def resolve_source(obj: BaseFile, context: dict[str, HttpRequest]) -> str:
        """Consider the BMA canonical URL the source if no other source has been specified."""
        return obj.source if obj.source else obj.get_absolute_url()


class SingleFileResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single file object."""

    bma_response: FileResponseSchema


class MultipleFileResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple file objects."""

    bma_response: list[FileResponseSchema]
