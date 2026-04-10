from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.schedule.models import Webstream, WebstreamMetadata
from api.schedule.serializers import (
    WebstreamMetadataSerializer,
    WebstreamSerializer,
)


@final
class WebstreamViewSet(viewsets.ModelViewSet[Any]):

    queryset = Webstream.objects.all()
    serializer_class: type[Serializer[Any]] = WebstreamSerializer
    model_permission_name: str = "webstream"

    def perform_create(self, serializer: WebstreamSerializer) -> None:
        """Create webstream with current user as owner (if authenticated)."""
        if self.request.user.is_authenticated:
            serializer.save(owner=self.request.user)
        else:
            serializer.save()


@final
class WebstreamMetadataViewSet(viewsets.ModelViewSet[Any]):

    queryset = WebstreamMetadata.objects.all()
    serializer_class: type[Serializer[Any]] = WebstreamMetadataSerializer
    model_permission_name: str = "webstreammetadata"
