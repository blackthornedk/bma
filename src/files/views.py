import logging
import re
from pathlib import Path
from urllib.parse import quote
from users.models import User

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import assign_perm
from django.core.exceptions import PermissionDenied

from audios.models import Audio
from documents.models import Document
from files.forms import UploadForm
from files.mixins import FilesApprovalMixin
from files.models import BaseFile
from files.models import StatusChoices
from pictures.models import Picture
from videos.models import Video

logger = logging.getLogger("bma")


class FileUploadView(LoginRequiredMixin, FormView):
    template_name = "upload.html"
    form_class = UploadForm


class FileDetailView(LoginRequiredMixin, DetailView):
    template_name = "detail.html"


def bma_media_view(request, path, accel):
    """Serve media files using nginx x-accel-redirect, or serve directly for dev use."""
    # get last uuid from the path
    if match := re.match(
        r"^.*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).*$",
        path,
    ):
        # get the file from database
        try:
            dbfile = BaseFile.objects.get(uuid=match.group(1))
        except BaseFile.DoesNotExist:
            logger.debug(
                f"File UUID {match.group(1)} not found in database, returning 404",
            )
            raise Http404()

        # check file permissions
        if not request.user.has_perm("files.view_basefile", dbfile) and not User.get_anonymous().has_perm("files.view_basefile", dbfile):
            # neither the current user nor the anonymous user has permissions to view this file
            raise PermissionDenied

        # check if the file exists in the filesystem
        if not Path(dbfile.original.path).exists():
            raise Http404()

        # OK, show the file
        if accel:
            # we are using nginx x-accel-redirect
            response = HttpResponse(status=200)
            # remove the Content-Type header to allow nginx to add it
            del response["Content-Type"]
            response["X-Accel-Redirect"] = f"/public/{quote(path)}"
        else:
            # we are serving the file locally
            f = open(Path(settings.MEDIA_ROOT) / Path(path), "rb")
            response = FileResponse(f, status=200)
        # all good
        return response
    else:
        # regex parsing failed
        logger.debug("Unable to parse filename regex to find file UUID, returning 404")
        raise Http404()


class FileBrowserView(TemplateView):
    template_name = "filebrowser.html"
