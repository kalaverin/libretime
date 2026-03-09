from typing import final

from rest_framework import viewsets

from libretime_api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from libretime_api.schedule.serializers import (
    SmartBlockContentSerializer,
    SmartBlockCriteriaSerializer,
    SmartBlockSerializer,
)


@final
class SmartBlockViewSet(viewsets.ModelViewSet):
    queryset = SmartBlock.objects.all()
    serializer_class = SmartBlockSerializer
    model_permission_name: str = "smartblock"


@final
class SmartBlockContentViewSet(viewsets.ModelViewSet):
    queryset = SmartBlockContent.objects.all()
    serializer_class = SmartBlockContentSerializer
    model_permission_name: str = "smartblockcontent"


@final
class SmartBlockCriteriaViewSet(viewsets.ModelViewSet):
    queryset = SmartBlockCriteria.objects.all()
    serializer_class = SmartBlockCriteriaSerializer
    model_permission_name: str = "smartblockcriteria"
