import re
from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ModelSerializer, ValidationError

from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
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
class SmartBlockSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = SmartBlock
        fields: str = "__all__"


@final
class SmartBlockContentSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = SmartBlockContent
        fields: str = "__all__"
        extra_kwargs = {
            "block": {"required": True},
            "file": {"required": True},
        }

    def validate_cue_in(self, value: Any) -> Any:
        """Validate cue_in doesn't contain path patterns (T479)."""
        if isinstance(value, str):
            validate_no_path_patterns(value, "cue_in")
        return value

    def validate_cue_out(self, value: Any) -> Any:
        """Validate cue_out doesn't contain path patterns (T479)."""
        if isinstance(value, str):
            validate_no_path_patterns(value, "cue_out")
        return value


@final
class SmartBlockCriteriaSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = SmartBlockCriteria
        fields: str = "__all__"
