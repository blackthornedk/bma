"""This module defines the table used to show files."""
import django_tables2 as tables
from albums.models import Album
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import BaseFile


class FileTable(tables.Table):
    """Defines the django-tables2 used to show files."""

    selection = tables.CheckBoxColumn(accessor="pk", orderable=False)
    uuid = tables.Column(linkify=True)
    albums = tables.Column(verbose_name="Albums")

    def render_albums(self, record: BaseFile) -> str:
        """Render albums as a list of links."""
        output = ""
        for album in Album.objects.filter(
            memberships__basefile__pk__contains=record.pk, memberships__period__contains=timezone.now()
        ):
            output += (
                '<a href="' + reverse("albums:album_detail", kwargs={"pk": album.pk}) + '">' + album.title + "</a><br>"
            )
        return mark_safe(output)  # noqa: S308

    class Meta:
        """Define model, template, fields."""

        model = BaseFile
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "selection",
            "uuid",
            "title",
            "albums",
            "attribution",
            "uploader",
            "license",
            "file_size",
            "approved",
            "published",
            "deleted",
        )
