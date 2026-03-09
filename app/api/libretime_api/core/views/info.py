from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from libretime_api.core.models import Preference
from libretime_api.core.serializers import InfoSerializer, VersionSerializer


class VersionView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VersionSerializer

    def get(self, request):
        return Response({"api_version": settings.API_VERSION})


class InfoView(APIView):
    permission_classes = [AllowAny]
    serializer_class = InfoSerializer

    def get(self, request):
        data = Preference.get_site_preferences()
        return Response(
            data.model_dump(
                include={
                    "station_name",
                },
            ),
        )
