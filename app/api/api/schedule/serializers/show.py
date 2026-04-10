from typing import Any

from django.db.models import Model
from rest_framework.serializers import ModelSerializer
from typing_extensions import final

from api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)


@final
class ShowSerializer(ModelSerializer[Any]):

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


@final
class ShowDaysSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = ShowDays
        fields: str = "__all__"


@final
class ShowHostSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = ShowHost
        fields: str = "__all__"


@final
class ShowInstanceSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = ShowInstance
        fields: str = "__all__"


@final
class ShowRebroadcastSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = ShowRebroadcast
        fields: str = "__all__"
