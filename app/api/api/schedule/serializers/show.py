from rest_framework import serializers

from api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)


class ShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Show
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
class ShowDaysSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = ShowDays
        fields: str = "__all__"


@final
class ShowHostSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = ShowHost
        fields: str = "__all__"


@final
class ShowInstanceSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = ShowInstance
        fields: str = "__all__"


@final
class ShowRebroadcastSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = ShowRebroadcast
        fields: str = "__all__"
