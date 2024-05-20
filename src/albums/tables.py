"""This module defines the table used to show albums."""
import django_tables2 as tables

from .models import Album


class AlbumTable(tables.Table):
    """Defines the django-tables2 used to show albums."""

    uuid = tables.Column(linkify=True)

    class Meta:
        """Define model, template, fields."""

        model = Album
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "uuid",
            "title",
            "description",
            "owner",
            "active_memberships",
            "historic_memberships",
            "future_memberships",
        )
