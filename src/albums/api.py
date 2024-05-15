"""The albums API."""
import logging
import operator
import uuid
from functools import reduce

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm
from ninja import Query
from ninja import Router
from utils.api import AlbumApiResponseType
from utils.schema import ApiMessageSchema

from .filters import AlbumFilters
from .models import Album
from .schema import AlbumRequestSchema
from .schema import MultipleAlbumResponseSchema
from .schema import SingleAlbumResponseSchema

logger = logging.getLogger("bma")

# initialise API router
router = Router()

# https://django-ninja.rest-framework.com/guides/input/query-params/#using-schema
query = Query(...)  # type: ignore[type-arg]


@router.post(
    "/create/",
    response={
        201: SingleAlbumResponseSchema,
        422: ApiMessageSchema,
    },
    summary="Create a new album",
)
def album_create(request: HttpRequest, payload: AlbumRequestSchema) -> AlbumApiResponseType:
    """Use this endpoint to create a new album, with or without files."""
    album = Album()
    for k, v in payload.dict().items():
        if k == "files":
            album.files.set(v)
        else:
            setattr(album, k, v)

    # set album owner
    album.owner = request.user  # type: ignore[assignment]

    # validate everything
    try:
        album.full_clean()
    except ValidationError:
        logger.exception("validation failed")
        return 422, ApiMessageSchema(message="Validation error")

    album.save()

    # assign permissions and return response
    assign_perm("change_album", request.user, album)
    assign_perm("delete_album", request.user, album)
    return 201, {"bma_response": album}


@router.get(
    "/{album_uuid}/",
    response={200: SingleAlbumResponseSchema, 404: ApiMessageSchema},
    summary="Return an album.",
    auth=None,
)
def album_get(request: HttpRequest, album_uuid: uuid.UUID) -> AlbumApiResponseType:
    """Return an album."""
    album = get_object_or_404(Album, uuid=album_uuid)
    return 200, {"bma_response": album}


@router.get(
    "/",
    response={200: MultipleAlbumResponseSchema},
    summary="Return a list of albums.",
    auth=None,
)
def album_list(request: HttpRequest, filters: AlbumFilters = query) -> AlbumApiResponseType:
    """Return a list of albums."""
    albums = Album.objects.all()

    if filters.files:
        # __in is OR and we want AND, build a query for .exclude() with all file UUIDs
        query = reduce(operator.and_, (Q(files__uuid=uuid) for uuid in filters.files))
        albums = albums.exclude(~query)

    if filters.search:
        albums = albums.filter(title__icontains=filters.search) | albums.filter(
            description__icontains=filters.search,
        )

    if filters.sorting:
        if filters.sorting.endswith("_asc"):
            # remove _asc and add +
            albums = albums.order_by(f"{filters.sorting[:-4]}")
        else:
            # remove _desc and add -
            albums = albums.order_by(f"-{filters.sorting[:-5]}")

    if filters.offset:
        albums = albums[filters.offset :]

    if filters.limit:
        albums = albums[: filters.limit]

    return 200, {"bma_response": albums}


@router.put(
    "/{album_uuid}/",
    response={
        200: SingleAlbumResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
    },
    operation_id="albums_api_album_update_put",
    summary="Replace an album.",
)
@router.patch(
    "/{album_uuid}/",
    response={
        200: SingleAlbumResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
    },
    operation_id="albums_api_album_update_patch",
    summary="Update an album.",
)
def album_update(
    request: HttpRequest,
    album_uuid: uuid.UUID,
    payload: AlbumRequestSchema,
    *,
    check: bool = False,
) -> AlbumApiResponseType:
    """Update (PATCH) or replace (PUT) an Album."""
    album = get_object_or_404(Album, uuid=album_uuid)
    if not request.user.has_perm("change_album", album):
        # no permission
        return 403, ApiMessageSchema(message="Permission denied.")
    if check:
        # check mode requested, don't change anything
        return 202, ApiMessageSchema(message="OK")
    if request.method == "PATCH":
        # we are updating the object, we do not want defaults for absent fields
        data = payload.dict(exclude_unset=True)
        # handle the m2m seperate
        del data["files"]
        Album.objects.filter(uuid=album.uuid).update(**data)
        album.refresh_from_db()
        if "files" in payload.dict():
            # we are updating the list of files, get a list of current and new file uuids
            current_uuids = set(album.active_files().values_list("uuid", flat=True))
            new_uuids = set(payload.dict()["files"])
            # get the list to be removed from the album
            remove_uuids = list(current_uuids.difference(new_uuids))
            album.remove_members(remove_uuids)
            # get the list of files to be added to the album
            add_uuids = new_uuids.difference(current_uuids)
            album.add_members(file_uuids=list(add_uuids))
    else:
        # we are replacing the object, we do want defaults for absent fields
        for attr, value in payload.dict(exclude_unset=False).items():
            if attr == "files":
                # end all current memberships
                current_uuids = album.active_files().values_list("uuid", flat=True)
                album.remove_members(list(current_uuids))
                # add the new memberships
                album.add_members(file_uuids=value)
                continue
            # set the attribute on the album
            setattr(album, attr, value)
        album.save()
        album.refresh_from_db()
    return 200, {"bma_response": album}


@router.delete(
    "/{album_uuid}/",
    response={202: ApiMessageSchema, 204: None, 403: ApiMessageSchema, 404: ApiMessageSchema},
    summary="Delete an album.",
)
def album_delete(
    request: HttpRequest, album_uuid: uuid.UUID, *, check: bool = False
) -> tuple[int, ApiMessageSchema | None]:
    """Delete an album."""
    album = get_object_or_404(Album, uuid=album_uuid)
    if not request.user.has_perm("delete_album", album):
        # no permission
        return 403, ApiMessageSchema(message="Permission denied.")
    if check:
        # check mode requested, don't change anything
        return 202, ApiMessageSchema(message="OK")
    album.deleted = True
    album.save(update_fields=["deleted"])
    return 204, None
