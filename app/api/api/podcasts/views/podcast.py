from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.mixins import AutoAssignOwnerMixin
from api.podcasts.models import (
    ImportedPodcast,
    Podcast,
    PodcastEpisode,
    StationPodcast,
)
from api.podcasts.serializers import (
    ImportedPodcastSerializer,
    PodcastEpisodeSerializer,
    PodcastSerializer,
    StationPodcastSerializer,
)


@final
class PodcastViewSet(AutoAssignOwnerMixin, viewsets.ModelViewSet[Any]):

    queryset = Podcast.objects.all()
    serializer_class: type[Serializer[Any]] = PodcastSerializer
    model_permission_name: str = "podcast"

    def get_queryset(self) -> Any:
        """Filter by owner for BOLA prevention (T663, T727)."""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        # Admin and Manager can see all, Host can only see own
        if user.role not in [user.role.ADMIN, user.role.MANAGER]:
            return queryset.filter(owner=user)
        return queryset


@final
class PodcastEpisodeViewSet(viewsets.ModelViewSet[Any]):

    queryset = PodcastEpisode.objects.all()
    serializer_class: type[Serializer[Any]] = PodcastEpisodeSerializer
    model_permission_name: str = "podcastepisode"


@final
class StationPodcastViewSet(viewsets.ModelViewSet[Any]):

    queryset = StationPodcast.objects.all()
    serializer_class: type[Serializer[Any]] = StationPodcastSerializer
    model_permission_name: str = "station"


@final
class ImportedPodcastViewSet(viewsets.ModelViewSet[Any]):

    queryset = ImportedPodcast.objects.all()
    serializer_class: type[Serializer[Any]] = ImportedPodcastSerializer
    model_permission_name: str = "importedpodcast"
