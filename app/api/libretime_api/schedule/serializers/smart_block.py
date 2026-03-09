from typing import final

from rest_framework import serializers

from libretime_api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)


@final
class SmartBlockSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = SmartBlock
        fields: str = "__all__"


@final
class SmartBlockContentSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = SmartBlockContent
        fields: str = "__all__"


@final
class SmartBlockCriteriaSerializer(serializers.ModelSerializer):
    @final
    class Meta:
        model = SmartBlockCriteria
        fields: str = "__all__"
