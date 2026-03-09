from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ModelSerializer

from api.schedule.models import Webstream, WebstreamMetadata


@final
class WebstreamSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Webstream
        fields: str = "__all__"


@final
class WebstreamMetadataSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = WebstreamMetadata
        fields: str = "__all__"
