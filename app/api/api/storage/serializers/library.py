from typing import Any

from django.db import models
from rest_framework import serializers
from typing_extensions import final

from api.storage.models import Library


@final
class LibrarySerializer(serializers.ModelSerializer[Any]):

    class Meta:
        model: type[models.Model] = Library
        fields: str = "__all__"
