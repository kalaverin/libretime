from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from api.schedule.serializers import (
    SmartBlockContentSerializer,
    SmartBlockCriteriaSerializer,
    SmartBlockSerializer,
)


@final
class SmartBlockViewSet(viewsets.ModelViewSet[Any]):

    queryset = SmartBlock.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockSerializer
    model_permission_name: str = "smartblock"


@final
class SmartBlockContentViewSet(viewsets.ModelViewSet[Any]):

    queryset = SmartBlockContent.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockContentSerializer
    model_permission_name: str = "smartblockcontent"


@final
class SmartBlockCriteriaViewSet(viewsets.ModelViewSet[Any]):

    queryset = SmartBlockCriteria.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockCriteriaSerializer
    model_permission_name: str = "smartblockcriteria"
