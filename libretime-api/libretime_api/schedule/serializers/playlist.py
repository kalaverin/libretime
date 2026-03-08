from rest_framework import serializers

from libretime_api.schedule.models import Playlist, PlaylistContent


class PlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = "__all__"


class PlaylistContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistContent
        fields = "__all__"
