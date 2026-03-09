from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.core.models import ServiceRegister
from api.core.serializers import ServiceRegisterSerializer


@final
class ServiceRegisterViewSet(viewsets.ModelViewSet[Any]):

    queryset = ServiceRegister.objects.all()
    serializer_class: type[Serializer[Any]] = ServiceRegisterSerializer
    model_permission_name: str = "serviceregister"
