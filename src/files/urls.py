"""URLs for the files app."""
from django.urls import path

from files.views import FileBrowserView
from files.views import FileDetailView
from files.views import FileUploadView

app_name = "files"

urlpatterns = [
    path("", FileBrowserView.as_view(), name="browse"),
    path("upload/", FileUploadView.as_view(), name="upload"),
    path("<pk>/", FileDetailView.as_view(), name="detail"),
]
