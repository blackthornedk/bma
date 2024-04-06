from django.db import models
from ninja import Schema, ModelSchema
from typing import Union, Optional, Any, List
import datetime
from django.utils import timezone
from .request import context_request

class RequestMetadataSchema(Schema):
    """The schema used for the request object in the root of all responses."""
    request_time: datetime.datetime
    username: Optional[str]
    client_ip: Optional[str]

    @staticmethod
    def resolve_request_time(obj, context):
        return datetime.datetime.now()

    @staticmethod
    def resolve_username(obj, context):
        print("inside resolve_username")
        request = context["request"]
        return request.user.username

    @staticmethod
    def resolve_client_ip(obj, context):
        request = context["request"]
        return request.META["REMOTE_ADDR"]


class ApiMessageSchema(Schema):
    """The schema used for all API responses which are just messages."""

    bma_request: RequestMetadataSchema
    message: str = None
    details: dict = None


class ApiResponseSchema(ApiMessageSchema):
    """The schema used for all API responses which contain a bma_response object."""
    bma_response: Optional[Any]


class ObjectPermissionSchema(Schema):
    """The schema used to include current permissions for objects."""
    user_permissions: List[str]
    group_permissions: List[str]
    effective_permissions: List[str]
