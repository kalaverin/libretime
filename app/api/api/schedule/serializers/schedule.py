from typing import final

from rest_framework import serializers

from api.schedule.models import Schedule


@final
class ReadScheduleSerializer(serializers.ModelSerializer):

    @final
    class Meta:
        model = Schedule
        fields: str = "__all__"

    cue_out = serializers.DurationField(source="get_cue_out", read_only=True)
    ends_at = serializers.DateTimeField(source="get_ends_at", read_only=True)


@final
class WriteScheduleSerializer(serializers.ModelSerializer):

    @final
    class Meta:
        model = Schedule
        fields: str = "__all__"
