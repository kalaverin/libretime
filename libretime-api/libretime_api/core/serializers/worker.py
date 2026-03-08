from rest_framework import serializers

from libretime_api.core.models import CeleryTask, ThirdPartyTrackReference


class ThirdPartyTrackReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdPartyTrackReference
        fields = "__all__"


class CeleryTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CeleryTask
        fields = "__all__"
