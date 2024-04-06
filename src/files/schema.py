import os
from utils.schema import RequestMetadataSchema
from django.utils import timezone
from guardian.shortcuts import get_perms, get_user_perms, get_group_perms
import uuid
from pathlib import Path
from typing import List
from typing import Optional

from django.urls import reverse
from ninja import ModelSchema
from ninja import Schema

from .models import FileTypeChoices
from .models import LicenseChoices, license_urls
from .models import StatusChoices
from files.models import BaseFile, StatusChoices
from utils.filters import SortingChoices
from utils.schema import ApiMessageSchema, ApiResponseSchema, ObjectPermissionSchema
from utils.permissions import get_object_permissions_schema


class UploadRequestSchema(ModelSchema):
    """File metatata."""

    license: LicenseChoices
    title: str = ""
    description: str = ""
    source: str = ""
    thumbnail_url: str = ""

    class Config:
        model = BaseFile
        model_fields = [
            "license",
            "attribution",
            "title",
            "description",
            "source",
            "thumbnail_url",
        ]


class FileUpdateRequestSchema(ModelSchema):
    title: Optional[str] = ""
    description: Optional[str] = ""
    source: Optional[str] = ""
    attribution: Optional[str] = ""
    thumbnail_url: Optional[str] = ""

    class Config:
        model = BaseFile
        model_fields = [
            "title",
            "description",
            "source",
            "attribution",
            "thumbnail_url",
        ]


class SingleFileRequestSchema(Schema):
    """The schema used for requests involving a single file."""
    file_uuid: uuid.UUID


class MultipleFileRequestSchema(Schema):
    """The schema us ed for requests involving multiple files."""
    file_uuids: List[uuid.UUID]


"""Response schemas below here."""


class FileResponseSchema(ModelSchema):
    albums: List[uuid.UUID] = []
    filename: str
    links: dict
    filetype: str
    filetype_icon: str
    status: str
    status_icon: str
    size_bytes: int
    permissions: ObjectPermissionSchema
    license_name: str
    license_url: str

    class Config:
        model = BaseFile
        model_fields = [
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
        ]

    @staticmethod
    def resolve_albums(obj, context):
        return [str(x) for x in obj.albums.values_list("uuid", flat=True)]

    @staticmethod
    def resolve_filename(obj, context):
        return Path(obj.original.path).name

    @staticmethod
    def resolve_size_bytes(obj, context):
        if os.path.exists(obj.original.path):
            return obj.original.size
        else:
            return 0

    @staticmethod
    def resolve_links(obj, context):
        return obj.resolve_links(request=context["request"])

    @staticmethod
    def resolve_status(obj, context):
        return StatusChoices[obj.status].label

    @staticmethod
    def resolve_permissions(obj, context):
        return get_object_permissions_schema(obj, context["request"])

    @staticmethod
    def resolve_license_name(obj, context):
        return getattr(LicenseChoices, obj.license).label

    @staticmethod
    def resolve_license_url(obj, context):
        return license_urls[obj.license]

    @staticmethod
    def resolve_source(obj, context):
        """Consider the BMA canonical URL the source if no other source has been specified."""
        return obj.source if obj.source else obj.get_absolute_url()


class SingleFileResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single file object."""
    bma_response: FileResponseSchema


class MultipleFileResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple file objects."""
    bma_response: List[FileResponseSchema]
