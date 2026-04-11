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

    def get_queryset(self) -> Any:
        """Filter by owner for BOLA prevention (T808, T809).

        API-Key auth bypasses filtering (services have full access).
        """
        queryset = super().get_queryset()

        # API-Key auth (services) - full access
        if check_authorization_header(self.request):
            return queryset

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        # Admin and Manager can see all, Host can only see own
        if user.role not in [user.role.ADMIN, user.role.MANAGER]:
            return queryset.filter(owner=user)
        return queryset


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
        playlist_id = self.request.query_params.get("playlist")
        if playlist_id:
            # Validate playlist_id to prevent SQLi and 500 errors (T357)
            try:
                validate_integer_id(playlist_id, "playlist")
                queryset = queryset.filter(playlist_id=playlist_id)
            except Exception:
                # Return empty queryset for invalid IDs
                return queryset.none()
        return queryset
