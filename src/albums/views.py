"""Album views."""
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models import Q
from django.db.models import QuerySet
from django.forms import Form
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import DetailView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from files.models import BaseFile
from guardian.shortcuts import get_objects_for_user

from .filters import AlbumFilter
from .models import Album
from .tables import AlbumTable


class AlbumListView(SingleTableMixin, FilterView):
    """Album list view."""

    model = Album
    table_class = AlbumTable
    template_name = "album_list.html"
    filterset_class = AlbumFilter
    context_object_name = "albums"

    def get_queryset(self) -> QuerySet[Album]:
        """Add membership counts."""
        qs = super().get_queryset()
        active_memberships = Count("memberships", filter=Q(memberships__period__contains=timezone.now()))
        historic_memberships = Count("memberships", filter=Q(memberships__period__endswith__lt=timezone.now()))
        future_memberships = Count("memberships", filter=Q(memberships__period__startswith__gt=timezone.now()))
        return qs.annotate(  # type: ignore[no-any-return]
            active_memberships=active_memberships,
            historic_memberships=historic_memberships,
            future_memberships=future_memberships,
        )


class AlbumDetailView(DetailView):  # type: ignore[type-arg]
    """Album detail view."""

    template_name = "album_detail.html"
    model = Album


class AlbumCreateView(LoginRequiredMixin, CreateView):  # type: ignore[type-arg]
    """Album create view."""

    template_name = "album_form.html"
    model = Album
    fields = ("title", "description", "files")

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:  # type: ignore[no-untyped-def] # noqa: ANN002,ANN003
        """Make sure user is in the curators group."""
        super().setup(request, *args, **kwargs)
        curator_group, created = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
        if curator_group not in request.user.groups.all():  # type: ignore[union-attr]
            raise PermissionDenied

    def get_form(self, form_class: Any | None = None) -> Form:  # noqa: ANN401
        """Return an instance of the form to be used in this view."""
        form = super().get_form()
        files = BaseFile.objects.filter(status="PUBLISHED").prefetch_related("uploader") | get_objects_for_user(
            self.request.user,
            "files.view_basefile",
        ).prefetch_related("uploader")
        form.fields["files"].queryset = files.distinct()
        return form  # type: ignore[no-any-return]

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Set album owner before saving."""
        album = form.save(commit=False)  # type: ignore[attr-defined]
        album.owner = self.request.user
        album.save()
        form.save_m2m()  # type: ignore[attr-defined]
        return HttpResponseRedirect(reverse_lazy("albums:detail", kwargs={"pk": album.uuid}))
