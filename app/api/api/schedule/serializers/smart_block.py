"""SmartBlock serializers with mass assignment protection."""

import re
from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ValidationError

from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from api.serializers import SecureModelSerializer, StrictSerializer
from api.validators.fields import (
    validate_choice,
    validate_duration_format,
    validate_foreign_key_id,
    validate_hex_color,
    validate_max_length,
    validate_non_negative_float,
    validate_non_negative_int,
    validate_not_empty_string,
    validate_not_null,
    validate_time_order,
)

# Pattern to detect path-like strings (T479)
_PATH_LIKE_PATTERN = re.compile(
    r"(?:\.\.)|(?:/)|(?:\\)"
)


def validate_no_path_patterns(value: str, field_name: str) -> str:
    """Validate that duration string doesn't contain path patterns."""
    if not isinstance(value, str):
        return value
    
    # Check for path traversal patterns (T479)
    if _PATH_LIKE_PATTERN.search(value):
        raise ValidationError(
            f"{field_name} contains invalid characters",
            code=f"{field_name}_invalid_chars",
        )
    return value


@final
class SmartBlockSerializer(SecureModelSerializer):
    """SmartBlock with full protection (has created_at/updated_at)."""

    class Meta:
        model: type[Model] = SmartBlock
        fields: str = "__all__"

    def validate_kind(self, value: Any) -> Any:
        """Validate kind is one of allowed choices (T837, T441)."""
        if value is not None:
            valid_kinds = {"static", "dynamic"}
            value = validate_choice(value, valid_kinds, "kind")
        return value

    def validate_name(self, value: Any) -> Any:
        """Validate name is not empty (T443)."""
        return validate_not_empty_string(value, "name")


@final
class SmartBlockContentSerializer(StrictSerializer):
    """SmartBlockContent with strict validation (no timestamp fields)."""

    class Meta:
        model: type[Model] = SmartBlockContent
        fields: str = "__all__"
        extra_kwargs = {
            "block": {"required": True},
            "file": {"required": True},
        }

    def validate_block(self, value: Any) -> Any:
        """Validate block ID is valid integer (T356)."""
        if isinstance(value, SmartBlock):
            return value
        return validate_foreign_key_id(value, "block")

    def validate_file(self, value: Any) -> Any:
        """Validate file ID is valid integer."""
        from api.storage.models import File
        if isinstance(value, File):
            return value
        return validate_foreign_key_id(value, "file")

    def validate_offset(self, value: Any) -> Any:
        """Validate offset is non-negative (T481)."""
        return validate_non_negative_float(value, "offset")

    def validate_cue_in(self, value: Any) -> Any:
        """Validate cue_in format (T483)."""
        if isinstance(value, str):
            validate_no_path_patterns(value, "cue_in")
        return validate_duration_format(value, "cue_in")

    def validate_cue_out(self, value: Any) -> Any:
        """Validate cue_out format (T483)."""
        if isinstance(value, str):
            validate_no_path_patterns(value, "cue_out")
        return validate_duration_format(value, "cue_out")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate time order (T482)."""
        cue_in = data.get("cue_in")
        cue_out = data.get("cue_out")
        validate_time_order(cue_in, cue_out)
        return super().validate(data)


@final
class SmartBlockCriteriaSerializer(StrictSerializer):
    """SmartBlockCriteria with strict validation (no timestamp fields)."""

    class Meta:
        model: type[Model] = SmartBlockCriteria
        fields: str = "__all__"
        extra_kwargs = {
            "block": {"required": True},
            "criteria": {"required": True},
            "condition": {"required": True},
            "value": {"required": True},
        }

    def validate_block(self, value: Any) -> Any:
        """Validate block ID is valid integer (T490, T367)."""
        if isinstance(value, SmartBlock):
            return value
        return validate_foreign_key_id(value, "block")

    def validate_value(self, value: Any) -> Any:
        """Validate value length (T499)."""
        return validate_max_length(value, 512, "value")

    def validate_group(self, value: Any) -> Any:
        """Validate group is non-negative (T500)."""
        return validate_non_negative_int(value, "group")

    def validate_criteria(self, value: Any) -> Any:
        """Validate criteria is one of allowed choices (T502)."""
        if value is not None:
            # Based on SmartBlock model - common criteria fields
            valid_criteria = {
                "album_title",
                "artist_name",
                "bit_rate",
                "bpm",
                "comments",
                "composer",
                "conductor",
                "copyright",
                "disc_number",
                "encoded_by",
                "encoder",
                "filename",
                "genre",
                "isrc_number",
                "label",
                "language",
                "length",
                "lyricist",
                "mood",
                "original_artist",
                "original_lyricist",
                "owner_id",
                "rating",
                "replay_gain",
                "sample_rate",
                "track_number",
                "year",
            }
            value = validate_choice(value, valid_criteria, "criteria")
        return value

    def validate_condition(self, value: Any) -> Any:
        """Validate condition is one of allowed choices (T503)."""
        if value is not None:
            valid_conditions = {
                "0",  # Contains
                "1",  # Does not contain
                "2",  # Is
                "3",  # Is not
                "4",  # Starts with
                "5",  # Ends with
                "6",  # Is greater than
                "7",  # Is less than
                "8",  # Is in the range
            }
            value = validate_choice(value, valid_conditions, "condition")
        return value

    def validate_value(self, value: Any) -> Any:
        """Validate value length (T499)."""
        return validate_max_length(value, 512, "value")
