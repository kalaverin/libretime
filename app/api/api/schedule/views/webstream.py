from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.mixins import AutoAssignOwnerMixin
from api.permissions import check_authorization_header
from api.schedule.models import Webstream, WebstreamMetadata
from api.schedule.serializers import (
    WebstreamMetadataSerializer,
    WebstreamSerializer,
)


@final
class WebstreamViewSet(AutoAssignOwnerMixin, viewsets.ModelViewSet[Any]):

    queryset = Webstream.objects.all()
    serializer_class: type[Serializer[Any]] = WebstreamSerializer
    model_permission_name: str = "webstream"


@final
class WebstreamMetadataViewSet(viewsets.ModelViewSet[Any]):

    queryset = WebstreamMetadata.objects.all()
    serializer_class: type[Serializer[Any]] = WebstreamMetadataSerializer
    model_permission_name: str = "webstreammetadata"
