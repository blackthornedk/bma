"""API schemas for the Audio model."""
from ninja import ModelSchema

from audios.models import Audio


class AudioOutSchema(ModelSchema):
    """ModelSchema for responses containing an instance of the Audio model."""

    class Config:
        """Include all fields."""

        model = Audio
        model_fields = "__all__"
