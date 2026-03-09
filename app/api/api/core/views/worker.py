from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.core.models import CeleryTask, ThirdPartyTrackReference
from api.core.serializers import (
    CeleryTaskSerializer,
    ThirdPartyTrackReferenceSerializer,
)


@final
class ThirdPartyTrackReferenceViewSet(viewsets.ModelViewSet[Any]):

    queryset = ThirdPartyTrackReference.objects.all()
    serializer_class: type[Serializer[Any]] = (
        ThirdPartyTrackReferenceSerializer
    )
    model_permission_name: str = "thirdpartytrackreference"


@final
class CeleryTaskViewSet(viewsets.ModelViewSet[Any]):

    queryset = CeleryTask.objects.all()
    serializer_class: type[Serializer[Any]] = CeleryTaskSerializer
    model_permission_name: str = "celerytask"
