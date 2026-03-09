from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ModelSerializer

from api.schedule.models import Playlist, PlaylistContent


@final
class PlaylistSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Playlist
        fields: str = "__all__"


@final
class PlaylistContentSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = PlaylistContent
        fields: str = "__all__"
