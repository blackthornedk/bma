from utils.filefield import MultipleFileField
from .models import BaseFile
from django import forms


class UploadForm(forms.ModelForm):
    files = MultipleFileField()

    class Meta:
        model = BaseFile
        fields = ["license", "attribution"]
