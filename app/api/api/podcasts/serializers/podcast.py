"""Podcast serializers with XSS protection."""

from typing import Any

from django.db.models import Model

from api.podcasts.models import (
    ImportedPodcast,
    Podcast,
    PodcastEpisode,
    StationPodcast,
)
from api.serializers import StrictSerializer
from api.validators.xss import validate_no_xss


class PodcastSerializer(StrictSerializer):
    """Podcast serializer with XSS protection."""

    class Meta:
        model: type[Model] = Podcast
        fields: str = "__all__"

    def validate_title(self, value: str) -> str:
        """Validate title field for XSS."""
        if value:
            validate_no_xss(value)
        return value

    def validate_description(self, value: str) -> str:
        """Validate description field for XSS."""
        if value:
            validate_no_xss(value)
        return value

    def validate_itunes_title(self, value: str) -> str:
        """Validate itunes_title field for XSS."""
        if value:
            validate_no_xss(value)
        return value


class PodcastEpisodeSerializer(StrictSerializer):
    """PodcastEpisode serializer with strict validation."""

    class Meta:
        model: type[Model] = PodcastEpisode
        fields: str = "__all__"


class StationPodcastSerializer(StrictSerializer):
    """StationPodcast serializer with strict validation."""

    class Meta:
        model: type[Model] = StationPodcast
        fields: str = "__all__"


class ImportedPodcastSerializer(StrictSerializer):
    """ImportedPodcast serializer with strict validation."""

    class Meta:
        model: type[Model] = ImportedPodcast
        fields: str = "__all__"
