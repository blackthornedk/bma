"""This module defines the table used to show files."""
import django_tables2 as tables

from .models import BaseFile


class FileTable(tables.Table):
    """Defines the django-tables2 used to show files."""

    selection = tables.CheckBoxColumn(accessor="pk", orderable=False)

    class Meta:
        """Define model, template, fields."""

        model = BaseFile
        template_name = "django_tables2/bootstrap.html"
        fields = ("uuid", "albums", "attribution", "uploader", "license", "file_size", "status", "title")
