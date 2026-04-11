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


class BlockIdQuerySetFilter:

    def get_queryset(self):
        queryset = super().get_queryset()

        if value := self.request.query_params.get("block"):
            try:
                validate_integer_id(value, "block")

            except Exception:
                # Return empty queryset for invalid IDs
                return queryset.none()

            queryset = queryset.filter(block_id=value)

        return queryset


@final
class SmartBlockContentViewSet(
    BlockIdQuerySetFilter, viewsets.ModelViewSet[Any],
):

    queryset = SmartBlockContent.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockContentSerializer
    model_permission_name: str = "smartblockcontent"
    filterset_fields = ["block"]
    filter_backends = [
        filters.OrderingFilter,
    ]
    ordering_fields = ["position"]
    ordering = ["position"]


@final
class SmartBlockCriteriaViewSet(
    BlockIdQuerySetFilter, viewsets.ModelViewSet[Any],
):

    queryset = SmartBlockCriteria.objects.all()
    serializer_class: type[Serializer[Any]] = SmartBlockCriteriaSerializer
    model_permission_name: str = "smartblockcriteria"
    filter_backends = [filters.OrderingFilter]
    filterset_fields = ["block"]
    ordering_fields = ["group", "criteria"]
    ordering = ["group", "criteria"]
