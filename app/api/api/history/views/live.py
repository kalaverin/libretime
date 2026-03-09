from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.history.models import LiveLog
from api.history.serializers import LiveLogSerializer


@final
class LiveLogViewSet(viewsets.ModelViewSet[Any]):
    queryset = LiveLog.objects.all()
    serializer_class: type[Serializer[Any]] = LiveLogSerializer
    model_permission_name: str = "livelog"
