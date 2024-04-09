"""API related utility functions."""
from albums.models import Album
from django.db.models import QuerySet
from files.models import BaseFile

from utils.schema import ApiResponseSchema


def wrap_response(
    payload: list[str] | dict[str, str] | QuerySet[Album] | QuerySet[BaseFile] | Album | BaseFile,
) -> ApiResponseSchema:
    """Wrap the response payload in the api envelope."""
    return ApiResponseSchema(bma_request=None, bma_response=payload)
