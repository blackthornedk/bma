from django.contrib import admin
from files.admin import BaseFileAdmin
from .models import Picture
from guardian.shortcuts import get_objects_for_user


@admin.register(Picture)
class PictureAdmin(BaseFileAdmin):
    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset()
        return get_objects_for_user(request.user, "view_basefile", klass=Picture)
