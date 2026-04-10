from typing import Any

from rest_framework import serializers

from api.history.models import (
    PlayoutHistory,
    PlayoutHistoryMetadata,
    PlayoutHistoryTemplate,
    PlayoutHistoryTemplateField,
)


class PlayoutHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayoutHistory
        fields = "__all__"

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate that ends is after starts."""
        starts = data.get("starts")
        ends = data.get("ends")

        if starts and ends and ends <= starts:
            raise serializers.ValidationError(
                {"ends": "End time must be after start time."},
            )

        return data


class PlayoutHistoryMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayoutHistoryMetadata
        fields = "__all__"


class PlayoutHistoryTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayoutHistoryTemplate
        fields = "__all__"


class PlayoutHistoryTemplateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayoutHistoryTemplateField
        fields = "__all__"
