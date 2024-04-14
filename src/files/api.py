"""The API of fileness."""
import logging
import uuid

import magic
from audios.models import Audio
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from documents.models import Document
from guardian.shortcuts import get_objects_for_user
from ninja import Query
from ninja import Router
from ninja.files import UploadedFile
from pictures.models import Picture
from utils.api import FileApiResponseType
from utils.schema import ApiMessageSchema
from videos.models import Video

from .filters import FileFilters
from .models import BaseFile
from .models import FileTypeChoices
from .schema import FileUpdateRequestSchema
from .schema import MultipleFileRequestSchema
from .schema import MultipleFileResponseSchema
from .schema import SingleFileRequestSchema
from .schema import SingleFileResponseSchema
from .schema import UploadRequestSchema

logger = logging.getLogger("bma")


# initialise API router
router = Router()

# https://django-ninja.rest-framework.com/guides/input/query-params/#using-schema
query: Query = Query(...)  # type: ignore[type-arg]


############## UPLOAD #########################################################
@router.post(
    "/upload/",
    response={
        201: SingleFileResponseSchema,
        403: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    summary="Upload a new file.",
)
def upload(request: HttpRequest, f: UploadedFile, metadata: UploadRequestSchema) -> FileApiResponseType:
    """API endpoint for file uploads."""
    # find the filetype using libmagic by reading the first bit of the file
    mime = magic.from_buffer(f.read(512), mime=True)

    if mime in settings.ALLOWED_PICTURE_TYPES:
        from pictures.models import Picture as Model
    elif mime in settings.ALLOWED_VIDEO_TYPES:
        from videos.models import Video as Model
    elif mime in settings.ALLOWED_AUDIO_TYPES:
        from audios.models import Audio as Model
    elif mime in settings.ALLOWED_DOCUMENT_TYPES:
        from documents.models import Document as Model
    else:
        return 422, ApiMessageSchema(message="File type not supported")

    uploaded_file = Model(
        owner=request.user,  # type: ignore[misc]
        original=f,
        original_filename=str(f.name),
        file_size=f.size,
        **metadata.dict(),
    )

    if not uploaded_file.title:
        # title defaults to the original filename
        uploaded_file.title = uploaded_file.original_filename

    if not uploaded_file.thumbnail_url:
        # thumbnail url was not specified, use the default for the filetype
        uploaded_file.thumbnail_url = settings.DEFAULT_THUMBNAIL_URLS[uploaded_file.filetype]

    try:
        uploaded_file.full_clean()
    except ValidationError:
        return 422, ApiMessageSchema(message="Validation error")

    # save everything
    uploaded_file.save()

    # if the filetype is picture then use the pictures large_thumbnail as thumbnail,
    # this has to be done after .save() to ensure the uuid filename and
    # full path is passed to the imagekit namer
    if (
        uploaded_file.filetype == "picture"
        and uploaded_file.thumbnail_url == settings.DEFAULT_THUMBNAIL_URLS["picture"]
    ):
        # use the large_thumbnail size as default
        uploaded_file.thumbnail_url = uploaded_file.large_thumbnail.url
        uploaded_file.save(update_fields=["thumbnail_url", "updated"])

    # assign permissions (publish_basefile and unpublish_basefile are assigned after moderation)
    uploaded_file.add_initial_permissions()

    # all good
    return 201, {"bma_response": uploaded_file, "message": f"File {uploaded_file.uuid} uploaded OK!"}


############## LIST ###########################################################
@router.get(
    "/",
    response={200: MultipleFileResponseSchema},
    summary="Return a list of metadata for files.",
    auth=None,
)
def file_list(request: HttpRequest, filters: FileFilters = query) -> FileApiResponseType:  # noqa: C901,PLR0912
    """Return a list of metadata for files."""
    # start out with a list of all PUBLISHED files plus whatever else the user has explicit access to
    files = BaseFile.objects.filter(status="PUBLISHED") | get_objects_for_user(
        request.user,
        "files.view_basefile",
    )
    files = files.distinct()

    if filters.albums:
        files = files.filter(albums__in=filters.albums)

    if filters.statuses:
        files = files.filter(status__in=filters.statuses)

    if filters.filetypes:
        query = Q()
        for filetype in filters.filetypes:
            # this could probably be more clever somehow
            if filetype == FileTypeChoices.picture:
                query |= Q(instance_of=Picture)
            elif filetype == FileTypeChoices.video:
                query |= Q(instance_of=Video)
            elif filetype == FileTypeChoices.audio:
                query |= Q(instance_of=Audio)
            elif filetype == FileTypeChoices.document:
                query |= Q(instance_of=Document)
        files = files.filter(query)

    if filters.owners:
        files = files.filter(owner__in=filters.owners)

    if filters.licenses:
        files = files.filter(license__in=filters.licenses)

    if filters.size:
        files = files.filter(file_size=filters.size)

    if filters.size_lt:
        files = files.filter(file_size__lt=filters.size_lt)

    if filters.size_gt:
        files = files.filter(file_size__gt=filters.size_gt)

    if filters.search:
        # we search title and description fields for now
        files = files.filter(title__icontains=filters.search) | files.filter(
            description__icontains=filters.search,
        )

    if filters.sorting:
        if filters.sorting.endswith("_asc"):
            # remove _asc
            files = files.order_by(f"{filters.sorting[:-4]}")
        else:
            # remove _desc and add -
            files = files.order_by(f"-{filters.sorting[:-5]}")

    if filters.offset:
        files = files[filters.offset :]

    if filters.limit:
        files = files[: filters.limit]

    return 200, {"bma_response": files}


############## GENERIC FILE ACTION ############################################
def api_file_action(  # noqa: PLR0913
    request: HttpRequest,
    file_uuids: list[uuid.UUID] | uuid.UUID,
    permission: str,
    old_status: str,
    action: str,
    *,
    check: bool,
) -> FileApiResponseType:
    """Perform an action on one or more files."""
    if isinstance(file_uuids, uuid.UUID):
        single = True
        file_uuids = [file_uuids]
    else:
        single = False
    file_filter: dict[str, str | list[str]] = {"uuid__in": [str(u) for u in file_uuids]}
    if old_status:
        file_filter["status"] = old_status
    db_files = get_objects_for_user(request.user, permission, klass=BaseFile.objects.filter(**file_filter))
    db_uuids = list(db_files.values_list("uuid", flat=True))
    logger.debug(
        f"user {request.user} wants to {action} {len(file_uuids)} files, has perm {permission} for {len(db_uuids)}"
    )
    if len(file_uuids) != db_files.count():
        errors = len(file_uuids) - db_files.count()
        return 403, ApiMessageSchema(
            message=f"Wrong status/no permission to {action} {errors} of {len(file_uuids)} files)"
        )
    if check:
        return 202, ApiMessageSchema(message="OK")
    updated = getattr(db_files, action)()
    logger.debug(f"{action} {updated} OK")
    db_files = BaseFile.objects.filter(
        uuid__in=db_uuids,
    )
    if single:
        db_files = db_files.get()
    return 200, {"bma_response": db_files, "message": f"{action} {len(db_uuids)} files OK"}


############## APPROVE ########################################################
def approve(request: HttpRequest, uuids: list[uuid.UUID] | uuid.UUID, *, check: bool) -> FileApiResponseType:
    """Approve one or more files by changing the status of a list of files from PENDING_MODERATION to UNPUBLISHED."""
    return api_file_action(
        request,
        uuids,
        "approve_basefile",
        old_status="PENDING_MODERATION",
        action="approve",
        check=check,
    )


@router.patch(
    "/{file_uuid}/approve/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Approve a file (change status from PENDING_MODERATION to UNPUBLISHED).",
)
def approve_file(
    request: HttpRequest, file_uuid: SingleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """API endpoint to change the status of a single file from PENDING_MODERATION to UNPUBLISHED."""
    return approve(request, file_uuid.file_uuid, check=check)


@router.patch(
    "/approve/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Approve multiple files (change status from PENDING_MODERATION to UNPUBLISHED).",
)
def approve_files(
    request: HttpRequest, payload: MultipleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """API endpoint to change the status of multiple files from PENDING_MODERATION to UNPUBLISHED."""
    uuids = payload.dict()["files"]
    return approve(request, uuids, check=check)


############## UNAPPROVE ######################################################
def unapprove(request: HttpRequest, uuids: list[uuid.UUID] | uuid.UUID, *, check: bool) -> FileApiResponseType:
    """Unapprove one or more files by changing the status of a list of files to PENDING_MODERATION."""
    return api_file_action(
        request,
        uuids,
        "unapprove_basefile",
        old_status="",
        action="unapprove",
        check=check,
    )


@router.patch(
    "/{file_uuid}/unapprove/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Unapprove a file (change status to PENDING_MODERATION).",
)
def unapprove_file(
    request: HttpRequest, file_uuid: SingleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """API endpoint to change the status of a single file to PENDING_MODERATION."""
    return unapprove(request, file_uuid.file_uuid, check=check)


@router.patch(
    "/unapprove/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Unapprove multiple files (change status to PENDING_MODERATION).",
)
def unapprove_files(
    request: HttpRequest, payload: MultipleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """API endpoint to change the status of multiple files to PENDING_MODERATION."""
    uuids = payload.dict()["files"]
    return unapprove(request, uuids, check=check)


############## PUBLISH ########################################################
def publish(request: HttpRequest, uuids: list[uuid.UUID] | uuid.UUID, *, check: bool) -> FileApiResponseType:
    """Publish a list of files by changing the status from UNPUBLISHED to PUBLISHED."""
    return api_file_action(
        request,
        uuids,
        "publish_basefile",
        old_status="UNPUBLISHED",
        action="publish",
        check=check,
    )


@router.patch(
    "/{file_uuid}/publish/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Publish a file (change status from UNPUBLISHED to PUBLISHED).",
)
def publish_file(
    request: HttpRequest, file_uuid: SingleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """API endpoint to change the status of a single file from UNPUBLISHED to PUBLISHED."""
    return publish(request, file_uuid.file_uuid, check=check)


@router.patch(
    "/publish/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Publish multiple files (change status from UNPUBLISHED to PUBLISHED).",
)
def publish_files(request: HttpRequest, data: MultipleFileRequestSchema, *, check: bool = False) -> FileApiResponseType:
    """Change the status of files from UNPUBLISHED to PUBLISHED."""
    files = data.dict()["files"]
    return publish(request, files, check=check)


############## UNPUBLISH ########################################################
def unpublish(request: HttpRequest, uuids: list[uuid.UUID] | uuid.UUID, *, check: bool) -> FileApiResponseType:
    """Unpublish a list of files by changing the status from PUBLISHED to UNPUBLISHED."""
    return api_file_action(
        request,
        uuids,
        "unpublish_basefile",
        old_status="PUBLISHED",
        action="unpublish",
        check=check,
    )


@router.patch(
    "/{file_uuid}/unpublish/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Unpublish a file (change status from PUBLISHED to UNPUBLISHED).",
)
def unpublish_file(
    request: HttpRequest, file_uuid: SingleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """API endpoint to change the status of a single file from PUBLISHED to UNPUBLISHED."""
    return unpublish(request, file_uuid.file_uuid, check=check)


@router.patch(
    "/unpublish/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Unpublish multiple files (change status from PUBLISHED to UNPUBLISHED).",
)
def unpublish_files(
    request: HttpRequest, data: MultipleFileRequestSchema, *, check: bool = False
) -> FileApiResponseType:
    """Change the status of files from PUBLISHED to UNPUBLISHED."""
    files = data.dict()["files"]
    return unpublish(request, files, check=check)


############## METADATA #######################################################
@router.get(
    "/{file_uuid}/",
    response={
        200: SingleFileResponseSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
    },
    summary="Return the metadata of a file.",
    auth=None,
)
def file_get(request: HttpRequest, file_uuid: uuid.UUID) -> FileApiResponseType:
    """Return a file object."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if basefile.status == "PUBLISHED" or request.user.has_perm(
        "view_basefile",
        basefile,
    ):
        return 200, {"bma_response": basefile}
    return 403, ApiMessageSchema(message="Permission denied.")


@router.put(
    "/{file_uuid}/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    operation_id="files_api_file_update_put",
    summary="Replace the metadata of a file.",
)
@router.patch(
    "/{file_uuid}/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    operation_id="files_api_file_update_patch",
    summary="Update the metadata of a file.",
)
def file_update(
    request: HttpRequest,
    file_uuid: uuid.UUID,
    metadata: FileUpdateRequestSchema,
    *,
    check: bool = False,
) -> FileApiResponseType:
    """Update (PATCH) or replace (PUT) a file metadata object."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("change_basefile", basefile):
        return 403, ApiMessageSchema(message="Permission denied.")
    if check:
        # check mode requested, don't change anything
        return 202, ApiMessageSchema(message="OK")
    if request.method == "PATCH":
        try:
            with transaction.atomic():
                # we are updating the object, we do not want defaults for absent fields
                BaseFile.objects.filter(uuid=basefile.uuid).update(
                    **metadata.dict(exclude_unset=True), updated=timezone.now()
                )
                basefile.refresh_from_db()
                basefile.full_clean()
        except ValidationError:
            return 422, ApiMessageSchema(message="Validation error")
    else:
        try:
            with transaction.atomic():
                # we are replacing the object, we do want defaults for absent fields
                BaseFile.objects.filter(uuid=basefile.uuid).update(
                    **metadata.dict(exclude_unset=False), updated=timezone.now()
                )
                basefile.refresh_from_db()
                basefile.full_clean()
        except ValidationError:
            return 422, ApiMessageSchema(message="Validation error")
    return 200, {"bma_response": basefile, "message": "File updated."}


############## DELETE #########################################################
@router.delete(
    "/{file_uuid}/",
    response={
        204: None,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
    },
    summary="Delete a file (change status to PENDING_DELETION).",
)
def file_delete(
    request: HttpRequest, file_uuid: uuid.UUID, *, check: bool = False
) -> tuple[int, ApiMessageSchema | None]:
    """Mark a file for deletion."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("delete_basefile", basefile):
        return 403, ApiMessageSchema(message="Permission denied.")
    if check:
        # check mode requested, don't change anything
        return 202, ApiMessageSchema(message="OK")
    # ok go but we don't let users fully delete files for now
    basefile.update_status(new_status="PENDING_DELETION")
    return 204, None
