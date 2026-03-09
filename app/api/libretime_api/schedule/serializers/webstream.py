from typing import final

from rest_framework import serializers

from libretime_api.schedule.models import Webstream, WebstreamMetadata


@final
class WebstreamSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = Webstream
        fields: str = "__all__"


@final
class WebstreamMetadataSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = WebstreamMetadata
        fields: str = "__all__"
