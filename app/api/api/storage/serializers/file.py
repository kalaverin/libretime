from typing import Any

from django.db import models
from rest_framework import serializers
from typing_extensions import final

from api.storage.models import File


@final
class FileSerializer(serializers.ModelSerializer[Any]):

    @final
    class Meta:
        model: type[models.Model] = File
        fields: str = "__all__"
