from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.core.models.role import Role
from api.permissions import check_authorization_header
from rest_framework.exceptions import PermissionDenied
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
        # Add creator as host (only for session-authenticated users, not API-Key)
        user = self.request.user
        if user.is_authenticated and not user.is_anonymous:
            from api.core.models import User

            if isinstance(user, User):
                ShowHost.objects.get_or_create(show=show, user=user)
        # Note: API-Key auth creates show without host (service-to-service)

    def _check_show_ownership(self, show: Show) -> None:
        """Verify user is host, manager, or admin before modifying a show."""
        from api.core.models.role import Role

        user = self.request.user
        # API-Key auth bypasses ownership check (services have full access)
        if check_authorization_header(self.request):
            return
        # Superuser (ADMIN) can modify any show
        is_super = user.is_superuser
        if callable(is_super):
            is_super = is_super()
        if is_super:
            return
        # MANAGER can modify any show (has full CRUD permissions)
        if user.role == Role.MANAGER:
            return
        # Host can modify their shows
        if show.hosts.filter(id=user.id).exists():
            return
        raise PermissionDenied("Only show hosts, managers, or admins can modify this show.")

    def perform_update(self, serializer: Any) -> None:
        """Update show - restricted to hosts and admins."""
        self._check_show_ownership(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance: Show) -> None:
        """Delete show - restricted to hosts and admins."""
        self._check_show_ownership(instance)
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
