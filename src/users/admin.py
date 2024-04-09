"""ModelAdmin for the User model."""
from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin[User]):
    """ModelAdmin for the User model."""

    list_display = ("username", "public_credit_name", "description")
    list_filter = ("username", "public_credit_name")
    search_fields = ("username", "public_credit_name", "description")
