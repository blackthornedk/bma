"""Widget related views."""

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render


def bma_widget(request: HttpRequest, style: str, count: int, uuid: str) -> HttpResponse:
    """Render a BMA widget rendered with the requested style, counter and UUID."""
    return render(
        request,
        f"{style}.js",
        context={"uuid": uuid, "count": count, "host": request.get_host()},
        content_type="text/javascript",
    )
