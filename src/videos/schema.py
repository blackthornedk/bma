"""API schemas for the Video model."""
from ninja import ModelSchema

from videos.models import Video


class VideoOutSchema(ModelSchema):
    """ModelSchema for responses containing an instance of the Video model."""

    class Config:
        """Include all fields."""

        model = Video
        model_fields = "__all__"
