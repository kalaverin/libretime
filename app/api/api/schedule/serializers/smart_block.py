from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ModelSerializer

from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)


@final
class SmartBlockSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = SmartBlock
        fields: str = "__all__"


@final
class SmartBlockContentSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = SmartBlockContent
        fields: str = "__all__"
        extra_kwargs = {
            "block": {"required": True},
            "file": {"required": True},
        }


@final
class SmartBlockCriteriaSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = SmartBlockCriteria
        fields: str = "__all__"
