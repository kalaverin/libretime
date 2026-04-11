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
from api.validators.race_conditions import validate_duplicate_url
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

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate duplicate URL (T722)."""
        url = data.get("url")
        owner = data.get("owner")

        # Get owner ID for validation
        if self.instance:
            owner_id = owner.id if owner else self.instance.owner_id
        else:
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                owner_id = request.user.id
            else:
                owner_id = None

        # T722: Check for duplicate URL per owner
        if url and owner_id:
            validate_duplicate_url(
                Podcast,
                url,
                owner_id,
                exclude_id=self.instance.id if self.instance else None,
            )

        return super().validate(data)


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
