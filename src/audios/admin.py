from django.contrib import admin
from files.admin import BaseFileAdmin
from guardian.shortcuts import get_objects_for_user

from .models import Audio


@admin.register(Audio)
class AudioAdmin(BaseFileAdmin):
    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset()
        return get_objects_for_user(request.user, "view_basefile", klass=Audio)
