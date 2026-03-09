from typing import final

from rest_framework import serializers

from api.schedule.models import Playlist, PlaylistContent


@final
class PlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields: str = "__all__"


@final
class PlaylistContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistContent
        fields: str = "__all__"
