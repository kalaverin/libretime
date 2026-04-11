from typing import Any, final

from django.db import models
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.mixins import ReadWriteSerializerMixin
from api.schedule.models import Schedule
from api.schedule.serializers import (
    ReadScheduleSerializer,
    WriteScheduleSerializer,
)


@final
class ScheduleFilter(filters.FilterSet):

    @final
    class Meta:
        model: type[models.Model] = Schedule
        fields: tuple[()] = ()

    starts = filters.DateTimeFromToRangeFilter(field_name="starts_at")
    ends = filters.DateTimeFromToRangeFilter(field_name="ends_at")
    position_status = filters.NumberFilter()
    broadcasted = filters.NumberFilter()
    instance = filters.NumberFilter(field_name="instance_id")

    overbooked = filters.BooleanFilter(method="overbooked_filter")

    # pylint: disable=unused-argument
    def overbooked_filter(self, queryset, name, value):
        # TODO: deduplicate code using the overbooked property
        if value:
            return queryset.filter(
                starts_at__gte=models.F("instance__ends_at"),
            )
        return queryset.filter(starts_at__lt=models.F("instance__ends_at"))


@final
class ScheduleViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet[Any]):

    queryset = Schedule.objects.all()
    read_serializer_class: type[Serializer[Any]] = ReadScheduleSerializer
    write_serializer_class: type[Serializer[Any]] = WriteScheduleSerializer
    filterset_class: type[filters.FilterSet] = ScheduleFilter
    model_permission_name: str = "schedule"
