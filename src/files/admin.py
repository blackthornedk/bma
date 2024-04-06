from django.contrib import admin
from django.utils.html import mark_safe
from guardian.admin import GuardedModelAdmin
from .models import BaseFile
from guardian.shortcuts import get_objects_for_user
from guardian.core import ObjectPermissionChecker
from django.contrib import messages
from django.utils.translation import ngettext
from utils.permissions import get_all_user_object_permissions
from utils.permissions import get_all_group_object_permissions

# disable deleting files through the admin for now
admin.site.disable_action("delete_selected")

@admin.register(BaseFile)
class BaseFileAdmin(admin.ModelAdmin):
    readonly_fields = ["status", "original_filename", "file_size", "license", "owner"]

    list_display = [
        "uuid",
        "owner",
        "thumbnail",
        "downloads",
        "permissions",
        "created",
        "updated",
        "title",
        "license",
        "attribution",
        "status",
    ]
    list_filter = ["license", "status"]

    actions = ["approve", "unapprove", "publish", "unpublish"]

    def get_actions(self, request):
        """Only enable an action if the user has permissions to perform the action."""
        actions = super().get_actions(request)
        valid_actions = actions.copy()
        for action in actions:
            if not get_objects_for_user(request.user, f"{action}_basefile", klass=BaseFile).exists():
                del valid_actions[action]
        return valid_actions

    def get_queryset(self, request):
        """Only return files the user has permissions to see."""
        if request.user.is_superuser:
            # superusers can see all files
            return super().get_queryset(request)
        return get_objects_for_user(request.user, "view_basefile", klass=BaseFile)

    def delete_queryset(self, request, queryset):
        """Soft delete."""
        queryset.update(status="PENDING_DELETION")

    def has_module_permission(self, request):
        """All users may see this modules index page."""
        return True

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("view_basefile", obj):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("change_basefile", obj):
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("delete_basefile", obj):
            return True
        return False

    def has_approve_basefile_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("approve_basefile", obj):
            print(f"user {request.user} has permission approve_basefile for file {obj}")
            return True
        return False

    def has_unapprove_basefile_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("unapprove_basefile", obj):
            print(f"user {request.user} has permission unapprove_basefile for file {obj}")
            return True
        return False

    def has_publish_basefile_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("publish_basefile", obj):
            return True
        return False

    def has_unpublish_basefile_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.has_perm("unpublish_basefile", obj):
            return True
        return False

    def send_message(self, request, selected, valid, updated, action):
        """Return a message to the user."""
        # set status
        if updated:
            if updated == valid:
                status = messages.SUCCESS
            else:
                status = messages.WARNING
        else:
            status = messages.ERROR
        # send message
        self.message_user(
            request,
            f"{selected} files selected to be {action}, out of those {valid} files had needed permission and expected status, and out of those {updated} files were successfully {action}",
            status,
        )

    @admin.action(description="Approve selected %(verbose_name_plural)s (switch status from PENDING_MODERATION to UNPUBLISHED)", permissions=["approve_basefile"])
    def approve(self, request, queryset):
        selected = queryset.count()
        valid = get_objects_for_user(request.user, 'files.approve_basefile', klass=queryset).filter(status="PENDING_MODERATION")
        valids = valid.count()
        updated = valid.approve()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="approved")

    @admin.action(description="Unapprove selected %(verbose_name_plural)s (switch status to PENDING_MODERATION)", permissions=["unapprove_basefile"])
    def unapprove(self, request, queryset):
        selected = queryset.count()
        valid = get_objects_for_user(request.user, 'files.unapprove_basefile', klass=queryset)
        valids = valid.count()
        updated = valid.unapprove()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="approved")

    @admin.action(description="Publish selected %(verbose_name_plural)s (switch status from UNPUBLISHED to PUBLISHED)", permissions=["publish_basefile"])
    def publish(self, request, queryset):
        selected = queryset.count()
        valid = get_objects_for_user(request.user, 'files.publish_basefile', klass=queryset).filter(status="UNPUBLISHED")
        valids = valid.count()
        updated = valid.publish()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="published")

    @admin.action(description="Unpublish selected %(verbose_name_plural)s (switch status from PUBLISHED to UNPUBLISHED)", permissions=["unpublish_basefile"])
    def unpublish(self, request, queryset):
        selected = queryset.count()
        valid = get_objects_for_user(request.user, 'files.unpublish_basefile', klass=queryset).filter(status="PUBLISHED")
        valids = valid.count()
        updated = valid.unpublish()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="unpublished")

    def permissions(self, obj):
        """Return all defined permissions for this object."""
        output = ""
        for perm in get_all_user_object_permissions(obj):
            output += f"user '{perm.user.username}' has '{perm.permission.codename}'<br>"
        for perm in get_all_group_object_permissions(obj):
            output += f"group '{perm.group}' has '{perm.permission.codename}'<br>"
        return mark_safe(output)

    def downloads(self, obj):
        """Return all download links for this object."""
        output = ""
        links = obj.resolve_links()
        for name, url in links["downloads"].items():
            output += f'<a href="{url}">{name}</a><br>'
        return mark_safe(output)

    def thumbnail(self, obj):
        try:
            return mark_safe(f'<a href="{obj.original.url}"><img src = "{obj.thumbnail_url}" width = "200"/></a>')
        except AttributeError:
            return ""
