"""API schemas for the Picture model."""
from ninja import ModelSchema

from pictures.models import Picture


class PictureOutSchema(ModelSchema):
    """ModelSchema for responses containing an instance of the Picture model."""

    class Config:
        """Include all fields."""

        model = Picture
        model_fields = "__all__"
