from rest_framework import viewsets

from libretime_api.schedule.models import Playlist, PlaylistContent
from libretime_api.schedule.serializers import (
    PlaylistContentSerializer,
    PlaylistSerializer,
)


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    model_permission_name = "playlist"


class PlaylistContentViewSet(viewsets.ModelViewSet):
    queryset = PlaylistContent.objects.all()
    serializer_class = PlaylistContentSerializer
    model_permission_name = "playlistcontent"
