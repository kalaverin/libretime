from typing import Any, final

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from api.core.models import Preference
from api.core.serializers import InfoSerializer, VersionSerializer
from api.permissions import PermissionsType


@final
class VersionView(APIView):

    permission_classes: PermissionsType = (AllowAny,)
    serializer_class: type[Serializer[Any]] = VersionSerializer

    def get(self, _: Request) -> Response:
        return Response({"api_version": settings.API_VERSION})


@final
class InfoView(APIView):

    permission_classes: PermissionsType = (AllowAny,)
    serializer_class: type[Serializer[Any]] = InfoSerializer

    def get(self, _: Request) -> Response:
        data = Preference.get_site_preferences()
        return Response(
            data.model_dump(
                include={
                    "station_name",
                },
            ),
        )
