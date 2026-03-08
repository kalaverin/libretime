from rest_framework import serializers

from libretime_api.storage.models import Library


class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = "__all__"
