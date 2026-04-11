from typing import Any, final

from rest_framework import filters, viewsets
from rest_framework.serializers import Serializer

from api.mixins import AutoAssignOwnerMixin
from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from api.schedule.serializers import (
    SmartBlockContentSerializer,
    SmartBlockCriteriaSerializer,
    SmartBlockSerializer,
)
from api.validators.fields import validate_integer_id


@final
class SmartBlockViewSet(AutoAssignOwnerMixin, viewsets.ModelViewSet[Any]):

    queryset = SmartBlock.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockSerializer
    model_permission_name: str = "smartblock"
    filter_backends = [filters.OrderingFilter]
    filterset_fields = ["kind"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self) -> Any:
        """Filter by owner for BOLA prevention (T829, T830, T831, T832)."""
        queryset = super().get_queryset()
        
        # BOLA fix: Only show blocks owned by current user
        # Admin and Manager can see all, Host can only see their own
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.role not in [user.role.ADMIN, user.role.MANAGER]:
            queryset = queryset.filter(owner=user)
        
        kind = self.request.query_params.get("kind")
        if kind:
            queryset = queryset.filter(kind=kind)
        return queryset


@final
class SmartBlockContentViewSet(viewsets.ModelViewSet[Any]):

    queryset = SmartBlockContent.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockContentSerializer
    model_permission_name: str = "smartblockcontent"
    filterset_fields = ["block"]
    filter_backends = [
        filters.OrderingFilter,
    ]
    ordering_fields = ["position"]
    ordering = ["position"]

    def get_queryset(self) -> Any:
        """Filter by block owner for BOLA prevention (T475, T476)."""
        queryset = super().get_queryset()
        
        # BOLA fix: Only show content from blocks owned by current user
        # Admin and Manager can see all, Host can only see their own
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.role not in [user.role.ADMIN, user.role.MANAGER]:
            queryset = queryset.filter(block__owner=user)
        
        block_id = self.request.query_params.get("block")
        if block_id:
            # Validate block_id to prevent SQLi and 500 errors (T356, T490)
            try:
                validate_integer_id(block_id, "block")
                queryset = queryset.filter(block_id=block_id)
            except Exception:
                # Return empty queryset for invalid IDs
                return queryset.none()
        return queryset


@final
class SmartBlockCriteriaViewSet(viewsets.ModelViewSet[Any]):

    queryset = SmartBlockCriteria.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockCriteriaSerializer
    model_permission_name: str = "smartblockcriteria"
    filter_backends = [filters.OrderingFilter]
    filterset_fields = ["block"]
    ordering_fields = ["group", "criteria"]
    ordering = ["group", "criteria"]

    def get_queryset(self) -> Any:
        """Filter by block owner for BOLA prevention (T488, T489, T496)."""
        queryset = super().get_queryset()
        
        # BOLA fix: Only show criteria from blocks owned by current user
        # Admin and Manager can see all, Host can only see their own
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.role not in [user.role.ADMIN, user.role.MANAGER]:
            queryset = queryset.filter(block__owner=user)
        
        block_id = self.request.query_params.get("block")
        if block_id:
            # Validate block_id to prevent SQLi and 500 errors (T367, T490)
            try:
                validate_integer_id(block_id, "block")
                queryset = queryset.filter(block_id=block_id)
            except Exception:
                # Return empty queryset for invalid IDs
                return queryset.none()
        return queryset
