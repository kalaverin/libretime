from typing import Any, final

from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.serializers import Serializer

from api.mixins import AutoAssignOwnerMixin
from api.permissions import check_authorization_header
from api.schedule.models import Playlist, PlaylistContent
from api.schedule.serializers import (
    PlaylistContentSerializer,
    PlaylistSerializer,
)
from api.validators.fields import validate_integer_id


@final
class PlaylistViewSet(AutoAssignOwnerMixin, viewsets.ModelViewSet[Any]):

    queryset = Playlist.objects.all()
    serializer_class: type[Serializer[Any]] = PlaylistSerializer
    model_permission_name: str = "playlist"


@final
class PlaylistContentViewSet(viewsets.ModelViewSet[Any]):

    queryset = PlaylistContent.objects.all()
    serializer_class: type[Serializer[Any]] = PlaylistContentSerializer
    model_permission_name: str = "playlistcontent"
    filter_backends = [OrderingFilter]
    filterset_fields = ["playlist"]
    ordering_fields = ["position"]
    ordering = ["position"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if value := self.request.query_params.get("playlist"):
            try:
                validate_integer_id(value, "playlist")

            except Exception:
                # Return empty queryset for invalid IDs
                return queryset.none()

            queryset = queryset.filter(playlist_id=value)

        return queryset
