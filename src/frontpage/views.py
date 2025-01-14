"""The frontpage view."""
import logging
from typing import Any

from audios.models import Audio
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from django.views.generic import TemplateView
from documents.models import Document
from files.models import BaseFile
from pictures.models import Picture
from users.models import User
from videos.models import Video

logger = logging.getLogger("bma")


class FrontpageTemplateView(TemplateView):
    """The frontpage view."""

    template_name = "frontpage.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, QuerySet[Picture]]:  # noqa: ANN401
        """Add recent files to the context."""
        context = super().get_context_data(**kwargs)
        context["6_last_pictures"] = self._query_last_6_uploads(self.request.user, "picture")
        context["6_last_videos"] = self._query_last_6_uploads(self.request.user, "video")
        context["6_last_audios"] = self._query_last_6_uploads(self.request.user, "audio")
        context["6_last_documents"] = self._query_last_6_uploads(self.request.user, "document")
        return context

    def _query_last_6_uploads(
        self, user: User | AnonymousUser, model: str
    ) -> QuerySet[Audio | Video | Picture | Document] | None:
        """Get the last 6 published uploads for a model."""
        try:
            return (  # type: ignore[no-any-return]
                BaseFile.bmanager.get_permitted(user=user)
                .filter(polymorphic_ctype__model=model)
                .order_by("created")[:6]
            )
        except BaseFile.DoesNotExist:
            return None
