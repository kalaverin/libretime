"""Show serializers with XSS protection."""

from typing import Any

from django.db.models import Model
from typing_extensions import final

from api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)
from api.serializers import SecureModelSerializer, StrictSerializer
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


@final
class ShowDaysSerializer(StrictSerializer):
    """ShowDays serializer with strict validation."""

    class Meta:
        model: type[Model] = ShowDays
        fields: str = "__all__"


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
