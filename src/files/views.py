"""File views."""
import logging
import re
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import TemplateView
from users.models import User

from files.forms import UploadForm
from files.models import BaseFile

logger = logging.getLogger("bma")


class FileUploadView(LoginRequiredMixin, FormView):  # type: ignore[type-arg]
    """The upload view of many files."""

    template_name = "upload.html"
    form_class = UploadForm


class FileDetailView(LoginRequiredMixin, DetailView):  # type: ignore[type-arg]
    """File detail view."""

    template_name = "detail.html"
    model = BaseFile


def bma_media_view(request: HttpRequest, path: str, *, accel: bool) -> FileResponse | HttpResponse:
    """Serve media files using nginx x-accel-redirect, or serve directly for dev use."""
    # get last uuid from the path
    match = re.match(
        r"^.*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).*$",
        path,
    )
    if not match:
        # regex parsing failed
        logger.debug("Unable to parse filename regex to find file UUID, returning 404")
        raise Http404

    # get the file from database
    try:
        dbfile = BaseFile.objects.get(uuid=match.group(1))
    except BaseFile.DoesNotExist as e:
        logger.debug(
            f"File UUID {match.group(1)} not found in database, returning 404",
        )
        raise Http404 from e

    # check file permissions
    if not request.user.has_perm("files.view_basefile", dbfile) and not User.get_anonymous().has_perm(  # type: ignore[attr-defined]
        "files.view_basefile", dbfile
    ):
        # neither the current user nor the anonymous user has permissions to view this file
        raise PermissionDenied

    # check if the file exists in the filesystem
    if not Path(dbfile.original.path).exists():
        raise Http404

    # OK, show the file
    response: FileResponse | HttpResponse
    if accel:
        # we are using nginx x-accel-redirect
        response = HttpResponse(status=200)
        # remove the Content-Type header to allow nginx to add it
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/public/{quote(path)}"
    else:
        # we are serving the file locally
        f = Path.open(Path(settings.MEDIA_ROOT) / Path(path), "rb")
        response = FileResponse(f, status=200)
    # all good
    return response


class FileBrowserView(TemplateView):
    """The file browser view."""

    template_name = "filebrowser.html"
