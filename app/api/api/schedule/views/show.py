from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.permissions import check_authorization_header
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

    queryset = Show.objects.all()  # Used by router for basename
    serializer_class: type[Serializer[Any]] = ShowSerializer
    model_permission_name: str = "show"

    def get_queryset(self) -> Any:
        """Filter shows by ownership - host sees only their shows, admin sees all, services see all."""
        request = self.request
        # API-Key auth (services) - full access
        if check_authorization_header(request):
            return Show.objects.all()
        # Session auth (users) - filter by ownership
        user = request.user
        if not user.is_authenticated:
            return Show.objects.none()
        if user.is_superuser():
            return Show.objects.all()
        # Host sees shows where they are assigned
        return Show.objects.filter(hosts=user).distinct()

    def perform_create(self, serializer: Any) -> None:
        """Create show and assign current user as host (for session auth)."""
        show = serializer.save()
        # Add creator as host (only for session-authenticated users, not API-Key)
        user = self.request.user
        if user.is_authenticated and not user.is_anonymous:
            from api.core.models import User

            if isinstance(user, User):
                ShowHost.objects.get_or_create(show=show, user=user)
        # Note: API-Key auth creates show without host (service-to-service)


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
