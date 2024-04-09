"""API schemas for the Document model."""
from ninja import ModelSchema

from documents.models import Document


class DocumentOutSchema(ModelSchema):
    """ModelSchema for responses containing an instance of the Document model."""

    class Config:
        """Include all fields."""

        model = Document
        model_fields = "__all__"
