from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.schedule.models import Playlist, PlaylistContent
from api.schedule.serializers import (
    PlaylistContentSerializer,
    PlaylistSerializer,
)


@final
class PlaylistViewSet(viewsets.ModelViewSet[Any]):

    queryset = Playlist.objects.all()
    serializer_class: type[Serializer[Any]] = PlaylistSerializer
    model_permission_name: str = "playlist"


@final
class PlaylistContentViewSet(viewsets.ModelViewSet[Any]):

    queryset = PlaylistContent.objects.all()
    serializer_class: type[Serializer[Any]] = PlaylistContentSerializer
    model_permission_name: str = "playlistcontent"
