from typing import Any

from django.db.models import Model
from rest_framework.serializers import ModelSerializer

from api.podcasts.models import (
    ImportedPodcast,
    Podcast,
    PodcastEpisode,
    StationPodcast,
)


class PodcastSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Podcast
        fields: str = "__all__"


class PodcastEpisodeSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = PodcastEpisode
        fields: str = "__all__"


class StationPodcastSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = StationPodcast
        fields: str = "__all__"


class ImportedPodcastSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = ImportedPodcast
        fields: str = "__all__"
