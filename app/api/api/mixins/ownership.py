"""
Ownership-related mixins for DRF ViewSets.
"""

from typing import Any

from rest_framework import serializers


class AutoAssignOwnerMixin:
    """
    Mixin that automatically assigns the current user as owner on create.

    Use this mixin with ModelViewSet for resources that have an 'owner' field.
    The mixin checks if:
    1. User is authenticated (not API-Key, not anonymous)
    2. User is a User instance (not AnonymousUser)
    3. Model has an 'owner' field

    Example:
        class PlaylistViewSet(AutoAssignOwnerMixin, viewsets.ModelViewSet):
            queryset = Playlist.objects.all()
            serializer_class = PlaylistSerializer
    """

    def perform_create(
        self,
        serializer: serializers.BaseSerializer[Any],
    ) -> None:
        """Create instance with current user as owner (if authenticated)."""
        user = self.request.user

        # Only assign owner for authenticated session users
        # API-Key auth should not auto-assign (services have their own logic)
        if not user.is_authenticated or user.is_anonymous:
            serializer.save()
            return

        # Check if user is a real User (not AnonymousUser)
        from api.core.models import User

        if not isinstance(user, User):
            serializer.save()
            return

        # Check if model has owner field
        model_class = serializer.Meta.model
        if not hasattr(model_class, "owner"):
            serializer.save()
            return

        # Save with owner
        serializer.save(owner=user)
