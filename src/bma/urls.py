"""BMA URL Configuration."""
from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path
from files.views import bma_media_view
from utils.views import csrfview

from .api import api_v1_json

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/json/", api_v1_json.urls),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("", include("frontpage.urls")),
    path("files/", include("files.urls", namespace="files")),
    path("api/csrf/", csrfview),
    path("widgets/", include("widgets.urls", namespace="widgets")),
]

# we are serving media files through nginx using X-Accel-Redirect in prod,
# and locally during development, determined by the value of 'accel' arg to bma_media_view
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)",
        bma_media_view,
        name="bma_media_view",
        kwargs={"accel": settings.NGINX_PROXY},
    ),
]
