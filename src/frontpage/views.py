"""The frontpage view."""
import logging
from typing import Any

from audios.models import Audio
from django.db.models import QuerySet
from django.views.generic import TemplateView
from documents.models import Document
from pictures.models import Picture
from videos.models import Video

logger = logging.getLogger("bma")


class FrontpageTemplateView(TemplateView):
    """The frontpage view."""

    template_name = "frontpage.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, QuerySet[Picture]]:  # noqa: ANN401
        """Add recent files to the context."""
        context = super().get_context_data(**kwargs)
        context["6_last_pictures"] = self._query_last_6_uploads(Picture)
        context["6_last_videos"] = self._query_last_6_uploads(Video)
        context["6_last_audios"] = self._query_last_6_uploads(Audio)
        context["6_last_documents"] = self._query_last_6_uploads(Document)
        return context

    def _query_last_6_uploads(
        self, model: type[Audio] | type[Video] | type[Picture] | type[Document]
    ) -> QuerySet[Audio | Video | Picture | Document] | None:
        """Get the last 6 published uploads for a model."""
        try:
            return model.objects.filter(  # type: ignore[no-any-return,misc]
                status="PUBLISHED"
            ).order_by(
                "created",
            )[:6]
        except model.doesnotexist:
            return None
