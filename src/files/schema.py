import os
import uuid
from pathlib import Path
from typing import List
from typing import Optional

from django.urls import reverse
from ninja import ModelSchema
from ninja import Schema

from .models import FileTypeChoices
from .models import LicenseChoices
from .models import StatusChoices
from files.models import BaseFile
from utils.schema import ListFilters
from utils.schema import SortingChoices


class UploadMetadata(ModelSchema):
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


class FileOutSchema(ModelSchema):
    albums: List[uuid.UUID] = []
    filename: str
    links: dict
    filetype_icon: str
    status_icon: str
    size_bytes: int
    filetype: str

    class Config:
        model = BaseFile
        model_fields = [
            "uuid",
            "owner",
            "created",
            "updated",
            "title",
            "description",
            "source",
            "license",
            "attribution",
            "status",
            "original_filename",
            "thumbnail_url",
        ]

    def resolve_albums(self, obj):
        return [str(x) for x in obj.albums.values_list("uuid", flat=True)]

    def resolve_filename(self, obj):
        return Path(obj.original.path).name

    def resolve_size_bytes(self, obj):
        if os.path.exists(obj.original.path):
            return obj.original.size
        else:
            return 0

    def resolve_links(self, obj):
        links = {
            "self": reverse("api-v1-json:file_get", kwargs={"file_uuid": obj.uuid}),
            "approve": reverse(
                "api-v1-json:file_approve",
                kwargs={"file_uuid": obj.uuid},
            ),
            "unpublish": reverse(
                "api-v1-json:file_unpublish",
                kwargs={"file_uuid": obj.uuid},
            ),
            "publish": reverse(
                "api-v1-json:file_publish",
                kwargs={"file_uuid": obj.uuid},
            ),
            "downloads": {
                "original": obj.original.url,
            },
        }
        if obj.filetype == "picture":
            try:
                links["downloads"].update(
                    {
                        "small_thumbnail": obj.small_thumbnail.url,
                        "medium_thumbnail": obj.medium_thumbnail.url,
                        "large_thumbnail": obj.large_thumbnail.url,
                        "small": obj.small.url,
                        "medium": obj.medium.url,
                        "large": obj.large.url,
                        "slideshow": obj.slideshow.url,
                    },
                )
            except OSError:
                # maybe file is missing from disk
                pass
        return links


class FileUpdateSchema(ModelSchema):
    title: Optional[str] = ""
    description: Optional[str] = ""
    source: Optional[str] = ""
    license: Optional[str] = ""
    attribution: Optional[str] = ""
    thumbnail_url: Optional[str] = ""

    class Config:
        model = BaseFile
        model_fields = [
            "title",
            "description",
            "source",
            "license",
            "attribution",
            "thumbnail_url",
        ]


class FileFilters(ListFilters):
    """The filters used for the file_list endpoint."""

    sorting: SortingChoices = None
    albums: List[uuid.UUID] = None
    statuses: List[StatusChoices] = None
    owners: List[uuid.UUID] = None
    licenses: List[LicenseChoices] = None
    filetypes: List[FileTypeChoices] = None
    size: int = None
    size_lt: int = None
    size_gt: int = None


class FileListSchema(Schema):
    files: List[uuid.UUID]
