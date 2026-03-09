from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.history.models import ListenerCount, MountName, Timestamp
from api.history.serializers import (
    ListenerCountSerializer,
    MountNameSerializer,
    TimestampSerializer,
)


@final
class MountNameViewSet(viewsets.ModelViewSet[Any]):

    queryset = MountName.objects.all()
    serializer_class: type[Serializer[Any]] = MountNameSerializer
    model_permission_name: str = "mountname"


@final
class TimestampViewSet(viewsets.ModelViewSet[Any]):

    queryset = Timestamp.objects.all()
    serializer_class: type[Serializer[Any]] = TimestampSerializer
    model_permission_name: str = "timestamp"


@final
class ListenerCountViewSet(viewsets.ModelViewSet[Any]):

    queryset = ListenerCount.objects.all()
    serializer_class: type[Serializer[Any]] = ListenerCountSerializer
    model_permission_name: str = "listenercount"
