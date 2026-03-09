from typing import final

from rest_framework import viewsets

from libretime_api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)
from libretime_api.schedule.serializers import (
    ShowDaysSerializer,
    ShowHostSerializer,
    ShowInstanceSerializer,
    ShowRebroadcastSerializer,
    ShowSerializer,
)


@final
class ShowViewSet(viewsets.ModelViewSet):
    queryset = Show.objects.all()
    serializer_class = ShowSerializer
    model_permission_name: str = "show"


@final
class ShowDaysViewSet(viewsets.ModelViewSet):
    queryset = ShowDays.objects.all()
    serializer_class = ShowDaysSerializer
    model_permission_name: str = "showdays"


@final
class ShowHostViewSet(viewsets.ModelViewSet):
    queryset = ShowHost.objects.all()
    serializer_class = ShowHostSerializer
    model_permission_name: str = "showhost"


@final
class ShowInstanceViewSet(viewsets.ModelViewSet):
    queryset = ShowInstance.objects.all()
    serializer_class = ShowInstanceSerializer
    model_permission_name: str = "showinstance"


@final
class ShowRebroadcastViewSet(viewsets.ModelViewSet):
    queryset = ShowRebroadcast.objects.all()
    serializer_class = ShowRebroadcastSerializer
    model_permission_name: str = "showrebroadcast"
