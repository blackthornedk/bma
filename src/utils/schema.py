"""API schemas used across multiple apps."""
import datetime
import logging
from typing import Any

from django.http import HttpRequest
from django.utils import timezone
from ninja import Schema

logger = logging.getLogger("bma")


class RequestMetadataSchema(Schema):
    """The schema used for the request object in the root of all responses."""

    request_time: datetime.datetime
    username: str
    client_ip: str

    @staticmethod
    def resolve_request_time(obj: dict[str, str]) -> datetime.datetime:
        """Get the value for the request_time field."""
        return timezone.now()

    @staticmethod
    def resolve_username(obj: dict[str, str], context: dict[str, HttpRequest]) -> str:
        """Get the value for the username field."""
        logger.debug(f"getting username from obj {obj} and context {context}")
        request = context["request"]
        return str(request.user.username)

    @staticmethod
    def resolve_client_ip(obj: dict[str, str], context: dict[str, HttpRequest]) -> str:
        """Get the value for the client_ip field."""
        request = context["request"]
        return str(request.META["REMOTE_ADDR"])


class ApiMessageSchema(Schema):
    """The schema used for all API responses which are just messages."""

    # TODO(tykling): figure out why 1) bma_request needs a default to work, and 2) why that default can't be the schema
    bma_request: RequestMetadataSchema = None  # type: ignore[assignment]
    message: str = "OK"
    details: dict[str, str] | None = None


class ApiResponseSchema(ApiMessageSchema):
    """The schema used for all API responses which contain a bma_response object."""

    bma_response: Any


class ObjectPermissionSchema(Schema):
    """The schema used to include current permissions for objects."""

    user_permissions: list[str]
    group_permissions: list[str]
    effective_permissions: list[str]
