from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.core.models import Preference
from api.core.serializers import PreferenceSerializer


@final
class PreferenceViewSet(viewsets.ModelViewSet[Any]):

    queryset = Preference.objects.all()
    serializer_class: type[Serializer[Any]] = PreferenceSerializer
    model_permission_name: str = "preference"
