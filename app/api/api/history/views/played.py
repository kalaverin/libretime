from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.history.models import (
    PlayoutHistory,
    PlayoutHistoryMetadata,
    PlayoutHistoryTemplate,
    PlayoutHistoryTemplateField,
)
from api.history.serializers import (
    PlayoutHistoryMetadataSerializer,
    PlayoutHistorySerializer,
    PlayoutHistoryTemplateFieldSerializer,
    PlayoutHistoryTemplateSerializer,
)


@final
class PlayoutHistoryViewSet(viewsets.ModelViewSet[Any]):

    queryset = PlayoutHistory.objects.all()
    serializer_class: type[Serializer[Any]] = PlayoutHistorySerializer
    model_permission_name: str = "playouthistory"


@final
class PlayoutHistoryMetadataViewSet(viewsets.ModelViewSet[Any]):

    queryset = PlayoutHistoryMetadata.objects.all()
    serializer_class: type[Serializer[Any]] = PlayoutHistoryMetadataSerializer
    model_permission_name: str = "playouthistorymetadata"


@final
class PlayoutHistoryTemplateViewSet(viewsets.ModelViewSet[Any]):

    queryset = PlayoutHistoryTemplate.objects.all()
    serializer_class: type[Serializer[Any]] = PlayoutHistoryTemplateSerializer
    model_permission_name: str = "playouthistorytemplate"


@final
class PlayoutHistoryTemplateFieldViewSet(viewsets.ModelViewSet[Any]):

    queryset = PlayoutHistoryTemplateField.objects.all()
    serializer_class: type[Serializer[Any]] = (
        PlayoutHistoryTemplateFieldSerializer
    )
    model_permission_name: str = "playouthistorytemplatefield"
