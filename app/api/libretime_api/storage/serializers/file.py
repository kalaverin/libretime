from typing import Any

from django.db import models
from rest_framework import serializers

from libretime_api.storage.models import File


class FileSerializer(serializers.ModelSerializer[Any]):

    class Meta:
        model: type[models.Model] = File
        fields: str = "__all__"
