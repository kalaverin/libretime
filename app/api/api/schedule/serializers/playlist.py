from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ValidationError

from api.schedule.models import Playlist, PlaylistContent
from api.serializers import SecureModelSerializer, StrictSerializer
from api.validators.fields import (
    validate_duration_format,
    validate_foreign_key_id,
    validate_non_negative_float,
    validate_non_negative_int,
)


@final
class PlaylistSerializer(SecureModelSerializer):
    """Playlist with full protection (has created_at/updated_at)."""

    class Meta:
        model: type[Model] = Playlist
        fields: str = "__all__"

    def validate_length(self, value: Any) -> Any:
        """Validate length format (T817)."""
        return validate_duration_format(value, "length")


@final
class PlaylistContentSerializer(StrictSerializer):
    """PlaylistContent with strict validation (no timestamp fields)."""

    class Meta:
        model: type[Model] = PlaylistContent
        fields: str = "__all__"
        extra_kwargs = {
            "playlist": {"required": True},
            "offset": {"required": False},
        }

    def validate_playlist(self, value: Any) -> Any:
        """Validate playlist ID is valid integer (T357)."""
        if isinstance(value, Playlist):
            return value
        return validate_foreign_key_id(value, "playlist")

    def validate_file(self, value: Any) -> Any:
        """Validate file ID is valid integer."""
        from api.storage.models import File

        if isinstance(value, File):
            return value
        return validate_foreign_key_id(value, "file")

    def validate_position(self, value: Any) -> Any:
        """Validate position is non-negative (T644)."""
        return validate_non_negative_int(value, "position")

    def validate_offset(self, value: Any) -> Any:
        """Validate offset is non-negative (T481)."""
        return validate_non_negative_float(value, "offset")

    def validate_length(self, value: Any) -> Any:
        """Validate length format (T817)."""
        return validate_duration_format(value, "length")

    def validate_cue_in(self, value: Any) -> Any:
        """Validate cue_in format (T483)."""
        return validate_duration_format(value, "cue_in")

    def validate_cue_out(self, value: Any) -> Any:
        """Validate cue_out format (T483)."""
        return validate_duration_format(value, "cue_out")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate that FILE kind has file assigned."""
        kind = data.get("kind")
        file_obj = data.get("file")

        if kind == PlaylistContent.Kind.FILE and not file_obj:
            raise ValidationError(
                {"file": "File is required when kind is FILE."},
            )

        return super().validate(data)
