from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)
from api.schedule.serializers import (
    ShowDaysSerializer,
    ShowHostSerializer,
    ShowInstanceSerializer,
    ShowRebroadcastSerializer,
    ShowSerializer,
)


@final
class ShowViewSet(viewsets.ModelViewSet[Any]):

    queryset = Show.objects.all()
    serializer_class: type[Serializer[Any]] = ShowSerializer
    model_permission_name: str = "show"


@final
class ShowDaysViewSet(viewsets.ModelViewSet[Any]):

    queryset = ShowDays.objects.all()
    serializer_class: type[Serializer[Any]] = ShowDaysSerializer
    model_permission_name: str = "showdays"


@final
class ShowHostViewSet(viewsets.ModelViewSet[Any]):

    queryset = ShowHost.objects.all()
    serializer_class: type[Serializer[Any]] = ShowHostSerializer
    model_permission_name: str = "showhost"


@final
class ShowInstanceViewSet(viewsets.ModelViewSet[Any]):

    queryset = ShowInstance.objects.all()
    serializer_class: type[Serializer[Any]] = ShowInstanceSerializer
    model_permission_name: str = "showinstance"


@final
class ShowRebroadcastViewSet(viewsets.ModelViewSet[Any]):

    queryset = ShowRebroadcast.objects.all()
    serializer_class: type[Serializer[Any]] = ShowRebroadcastSerializer
    model_permission_name: str = "showrebroadcast"
