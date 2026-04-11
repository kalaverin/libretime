from typing import Any

from django.db import models
from typing_extensions import final

from api.serializers import SecureModelSerializer
from api.storage.models import File
from api.storage.validators import validate_filepath


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
