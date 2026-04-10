from datetime import timedelta
from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ModelSerializer

from api.schedule.models import Webstream, WebstreamMetadata
from sdk import now


@final
class WebstreamSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Webstream
        fields: str = "__all__"
        extra_kwargs = {
            "created_at": {"required": False},
            "updated_at": {"required": False},
            "length": {"required": False},
        }

    def create(self, validated_data: dict[str, Any]) -> Webstream:
        """Create webstream with default values for optional fields."""
        # Set defaults for auto-populated fields
        current_time = now()
        validated_data.setdefault("created_at", current_time)
        validated_data.setdefault("updated_at", current_time)
        validated_data.setdefault("length", timedelta(seconds=0))

        return super().create(validated_data)

    def update(
        self, instance: Webstream, validated_data: dict[str, Any],
    ) -> Webstream:
        """Update webstream with auto-updated updated_at."""
        # Always update the updated_at timestamp
        validated_data["updated_at"] = now()

        return super().update(instance, validated_data)


@final
class WebstreamMetadataSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = WebstreamMetadata
        fields: str = "__all__"
