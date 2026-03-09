from rest_framework import serializers

from api.history.models import LiveLog


class LiveLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveLog
        fields = "__all__"
