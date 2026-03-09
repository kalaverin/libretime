from rest_framework import viewsets

from libretime_api.schedule.models import Webstream, WebstreamMetadata
from libretime_api.schedule.serializers import (
    WebstreamMetadataSerializer,
    WebstreamSerializer,
)


class WebstreamViewSet(viewsets.ModelViewSet):
    queryset = Webstream.objects.all()
    serializer_class = WebstreamSerializer
    model_permission_name = "webstream"


class WebstreamMetadataViewSet(viewsets.ModelViewSet):
    queryset = WebstreamMetadata.objects.all()
    serializer_class = WebstreamMetadataSerializer
    model_permission_name = "webstreametadata"
