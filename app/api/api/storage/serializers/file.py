from typing import Any

from django.db import models
from rest_framework import serializers
from typing_extensions import final

from api.storage.models import File
from api.storage.validators import validate_filepath


@final
class FileSerializer(serializers.ModelSerializer[Any]):

    class Meta:
        model: type[models.Model] = File
        fields: str = "__all__"

    def validate_filepath(self, value: Any) -> Any:
        """Validate filepath to prevent path traversal attacks."""
        validate_filepath(value)
        return value
