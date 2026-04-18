from typing import Any, final

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import Serializer

from api.permissions import (
    is_authenticated,
    is_superuser,
    request_superauthorized,
)
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

    def perform_create(self, serializer: Any) -> None:
        """Create show and assign current user as host (for session auth)."""

        show = serializer.save()
        user = self.request.user

        if is_authenticated(user) or is_superuser(user):
            ShowHost.objects.get_or_create(show=show, user=user)

        # API-Key auth: don't auto-assign host (services create shows without hosts)

    def check_ownership(self, show: Show) -> None:
        """Verify user is host, manager, or admin before modifying a show."""

        request = self.request
        if not (
            request_superauthorized(request)
            or show.hosts.filter(id=request.user.id).exists()
        ):
            raise PermissionDenied(
                "Only show hosts, managers, or admins can modify this show.",
            )

    def perform_update(self, serializer: Any) -> None:
        """Update show - restricted to hosts and admins."""
        self.check_ownership(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance: Show) -> None:
        """Delete show - restricted to hosts and admins."""
        self.check_ownership(instance)
        instance.delete()


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
