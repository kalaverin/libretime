from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.core.models import Preference


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = "__all__"
        # Remove unique validator from key field to allow same key for different users
        # The unique_together constraint on (user, key) is enforced by UniqueTogetherValidator
        extra_kwargs = {
            "key": {"validators": []},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Preference.objects.all(),
                fields=("user", "key"),
                message="Preference with this user and key already exists.",
            ),
        ]
