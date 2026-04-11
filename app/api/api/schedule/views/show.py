from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

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

    def get_queryset(self) -> Any:
        """Return all shows - schedule is public information.
        
        READ operations (LIST/RETRIEVE): All authenticated users see all shows.
        WRITE operations (UPDATE/DELETE): Restricted to hosts/admins in perform_* methods.
        """
        request = self.request
        # API-Key auth (services) - full access
        if check_authorization_header(request):
            return Show.objects.all()
        # Session auth (users) - shows are public schedule
        user = request.user
        if not user.is_authenticated:
            return Show.objects.none()
        # All authenticated users see all shows (broadcast schedule is public)
        return Show.objects.all()

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
        """Verify user is host or admin before modifying a show."""
        user = self.request.user
        # API-Key auth bypasses ownership check (services have full access)
        if check_authorization_header(self.request):
            return
        # Superuser can modify any show
        # Handle both method and property
        is_super = user.is_superuser
        if callable(is_super):
            is_super = is_super()
        if is_super:
            return
        # Host can modify their shows
        if show.hosts.filter(id=user.id).exists():
            return
        raise PermissionDenied("Only show hosts or admins can modify this show.")

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
