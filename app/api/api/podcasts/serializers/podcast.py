"""Podcast serializers with mass assignment protection."""

from typing import Any

from django.db.models import Model

from api.podcasts.models import (
    ImportedPodcast,
    Podcast,
    PodcastEpisode,
    StationPodcast,
)
from api.serializers import StrictSerializer


class PodcastSerializer(StrictSerializer):
    """Podcast serializer (no timestamp fields on model)."""

    class Meta:
        model: type[Model] = Podcast
        fields: str = "__all__"


class PodcastEpisodeSerializer(StrictSerializer):
    """PodcastEpisode serializer (no timestamp fields on model)."""

    class Meta:
        model: type[Model] = PodcastEpisode
        fields: str = "__all__"


class StationPodcastSerializer(StrictSerializer):
    """StationPodcast serializer (no timestamp fields on model)."""

    class Meta:
        model: type[Model] = StationPodcast
        fields: str = "__all__"


class ImportedPodcastSerializer(StrictSerializer):
    """ImportedPodcast serializer (no timestamp fields on model)."""

    class Meta:
        model: type[Model] = ImportedPodcast
        fields: str = "__all__"
