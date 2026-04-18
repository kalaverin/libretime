"""Show serializers with XSS protection."""

from typing import Any

from django.db.models import Model
from rest_framework.serializers import ValidationError
from typing_extensions import final

from api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)
from api.serializers import SecureModelSerializer, StrictSerializer
from api.validators.fields import (
    validate_duration_format,
    validate_hex_color,
)
from api.validators.xss import validate_no_xss


@final
class ShowSerializer(SecureModelSerializer):
    """Show serializer with XSS protection."""

    class Meta:
        model: type[Model] = Show
        fields: tuple[str, ...] = (
            "id",
            "name",
            "description",
            "genre",
            "url",
            "image",
            "foreground_color",
            "background_color",
            "live_enabled",
            "live_auth_registered",
            "live_auth_custom",
            "live_auth_custom_user",
            "live_auth_custom_password",
            "linked",
            "linkable",
            "auto_playlist",
            "auto_playlist_enabled",
            "auto_playlist_repeat",
            "intro_playlist",
            "override_intro_playlist",
            "outro_playlist",
            "override_outro_playlist",
        )

    def validate_description(self, value: str) -> str:
        """Validate description field for XSS."""
        if value:
            validate_no_xss(value)
        return value

    def validate_url(self, value: str) -> str:
        """Validate URL field for XSS."""
        if value:
            validate_no_xss(value)
        return value

    def validate_background_color(self, value: str) -> str:
        """Validate background color is valid hex (T381)."""
        return validate_hex_color(value, "background_color")

    def validate_foreground_color(self, value: str) -> str:
        """Validate foreground color is valid hex (T381)."""
        return validate_hex_color(value, "foreground_color")


@final
class ShowDaysSerializer(StrictSerializer):
    """ShowDays serializer with strict validation."""

    class Meta:
        model: type[Model] = ShowDays
        fields: str = "__all__"

    def validate_duration(self, value: Any) -> Any:
        """Validate duration format [HH:]MM:SS[.ms] (T395)."""
        return validate_duration_format(value, "duration")

    def validate_last_show(self, value: Any) -> Any:
        """Validate last_show is not null when provided (T396)."""
        # Only validate if key is present in input data
        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate last_show is not null if provided (T396)."""
        # Check if last_show is explicitly set to None in initial data
        if hasattr(self, "initial_data") and "last_show" in self.initial_data:
            if self.initial_data["last_show"] is None:
                raise ValidationError(
                    {"last_show": "last_show cannot be null."},
                    code="last_show_null",
                )
        return super().validate(data)


@final
class ShowHostSerializer(StrictSerializer):
    """ShowHost serializer with strict validation."""

    class Meta:
        model: type[Model] = ShowHost
        fields: str = "__all__"


@final
class ShowInstanceSerializer(StrictSerializer):
    """ShowInstance serializer with strict validation."""

    class Meta:
        model: type[Model] = ShowInstance
        fields: str = "__all__"


@final
class ShowRebroadcastSerializer(StrictSerializer):
    """ShowRebroadcast serializer with strict validation."""

    class Meta:
        model: type[Model] = ShowRebroadcast
        fields: str = "__all__"
