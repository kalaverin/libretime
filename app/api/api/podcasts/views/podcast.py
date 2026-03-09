from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

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
class PodcastViewSet(viewsets.ModelViewSet[Any]):

    queryset = Podcast.objects.all()
    serializer_class: type[Serializer[Any]] = PodcastSerializer
    model_permission_name: str = "podcast"


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
