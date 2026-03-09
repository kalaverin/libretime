from rest_framework import serializers

from libretime_api.core.models import Preference

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = "__all__"
