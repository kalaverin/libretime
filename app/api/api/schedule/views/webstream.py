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

    def get_queryset(self) -> Any:
        """Filter webstreams by ownership - user sees only their own, admin sees all."""
        request = self.request
        # API-Key auth (services) - full access
        if check_authorization_header(request):
            return Webstream.objects.all()
        # Session auth (users) - filter by ownership
        user = request.user
        if not user.is_authenticated:
            return Webstream.objects.none()
        if user.is_superuser():
            return Webstream.objects.all()
        # Regular user sees only their own webstreams
        return Webstream.objects.filter(owner=user)


@final
class WebstreamMetadataViewSet(viewsets.ModelViewSet[Any]):

    queryset = WebstreamMetadata.objects.all()
    serializer_class: type[Serializer[Any]] = WebstreamMetadataSerializer
    model_permission_name: str = "webstreammetadata"
