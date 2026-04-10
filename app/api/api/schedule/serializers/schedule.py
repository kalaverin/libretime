from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import (
    DateTimeField,
    DurationField,
    ModelSerializer,
    ValidationError,
)

from api.schedule.models import Schedule


@final
class ReadScheduleSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Schedule
        fields: str = "__all__"

    cue_out = DurationField(source="get_cue_out", read_only=True)
    ends_at = DateTimeField(source="get_ends_at", read_only=True)


@final
class WriteScheduleSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Schedule
        fields: str = "__all__"

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate that either file or stream is provided."""
        file_obj = data.get("file")
        stream = data.get("stream")

        if not file_obj and not stream:
            raise ValidationError(
                {"file": "Either file or stream is required."}
            )

        return data
