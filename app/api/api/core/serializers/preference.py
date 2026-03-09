from rest_framework import serializers

from api.core.models import Preference


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = "__all__"
