"""The filters used for the file_list endpoint."""
import uuid

from utils.filters import ListFilters
from utils.filters import SortingChoices

from .models import FileTypeChoices
from .models import LicenseChoices
from .models import StatusChoices


class FileFilters(ListFilters):
    """The filters used for the file_list endpoint."""

    sorting: SortingChoices | None = None
    albums: list[uuid.UUID] | None = None
    statuses: list[StatusChoices] | None = None
    owners: list[uuid.UUID] | None = None
    licenses: list[LicenseChoices] | None = None
    filetypes: list[FileTypeChoices] | None = None
    size: int | None = None
    size_lt: int | None = None
    size_gt: int | None = None
