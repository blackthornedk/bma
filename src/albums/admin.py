"""ModelAdmin for the Album model."""
from django.contrib import admin

from .models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin[Album]):
    """ModelAdmin for the Album model."""

    list_display = (
        "uuid",
        "owner",
        "created",
        "updated",
        "title",
        "description",
    )
    list_filter = ("owner",)
