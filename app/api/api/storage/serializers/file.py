from typing import Any

from django.db import models
from typing_extensions import final

from api.serializers import SecureModelSerializer
from api.storage.models import File
from api.storage.validators import validate_filepath
from api.validators.fields import validate_non_negative_int
from api.validators.xss import validate_no_xss


@final
class FileSerializer(SecureModelSerializer):

    class Meta:
        model: type[models.Model] = File
        fields: str = "__all__"
        # id, owner, created_at, updated_at are protected by SecureModelSerializer

    def validate_filepath(self, value: Any) -> Any:
        """Validate filepath to prevent path traversal attacks."""
        validate_filepath(value)
        return value

    def validate_track_title(self, value: str) -> str:
        """Validate track_title field for XSS (T883)."""
        if value:
            validate_no_xss(value)
        return value

    def validate_channels(self, value: Any) -> Any:
        """Validate channels is non-negative (T900)."""
        return validate_non_negative_int(value, "channels")
