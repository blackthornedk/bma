"""URLs for the albums app."""
from django.urls import path

from .views import AlbumCreateView
from .views import AlbumDetailView
from .views import AlbumListView

app_name = "albums"

urlpatterns = [
    path("", AlbumListView.as_view(), name="album_list"),
    path("create/", AlbumCreateView.as_view(), name="album_create"),
    path("<pk>/", AlbumDetailView.as_view(), name="album_detail"),
]
