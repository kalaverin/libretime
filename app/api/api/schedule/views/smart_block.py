from typing import Any, final

from rest_framework import filters, viewsets
from rest_framework.serializers import Serializer

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


@final
class SmartBlockViewSet(viewsets.ModelViewSet[Any]):

    queryset = SmartBlock.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockSerializer
    model_permission_name: str = "smartblock"
    filter_backends = [filters.OrderingFilter]
    filterset_fields = ["kind"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self) -> Any:
        """Filter by kind if provided."""
        queryset = super().get_queryset()
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
        """Filter by block if provided."""
        queryset = super().get_queryset()
        block_id = self.request.query_params.get("block")
        if block_id:
            queryset = queryset.filter(block_id=block_id)
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
        """Filter by block if provided."""
        queryset = super().get_queryset()
        block_id = self.request.query_params.get("block")
        if block_id:
            queryset = queryset.filter(block_id=block_id)
        return queryset
