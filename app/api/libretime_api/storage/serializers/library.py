from typing import Any

from django.db import models
from rest_framework import serializers

from libretime_api.storage.models import Library


class LibrarySerializer(serializers.ModelSerializer[Any]):

    class Meta:
        model: type[models.Model] = Library
        fields: str = "__all__"
