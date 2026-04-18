"""Library serializer with mass assignment protection."""

from django.db import models
from typing_extensions import final

from api.serializers import StrictSerializer
from api.storage.models import Library


@final
class LibrarySerializer(StrictSerializer):
    """Library serializer (no timestamp fields on model)."""

    class Meta:
        model: type[models.Model] = Library
        fields: str = "__all__"
