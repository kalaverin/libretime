from typing import Any, final

from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from api.core.models import Preference
from api.core.serializers import (
    StreamPreferencesSerializer,
    StreamStateSerializer,
)
from api.permissions import (
    IsSystemTokenOrUser,
    PermissionsType,
)


@final
class StreamPreferencesView(views.APIView):

    serializer_class: type[Serializer[Any]] = StreamPreferencesSerializer
    permission_classes: PermissionsType = (IsSystemTokenOrUser,)
    model_permission_name: str = "streamsetting"

    def get(self, _: Request) -> Response:
        data = Preference.get_stream_preferences()
        return Response(
            data.model_dump(
                include={
                    "input_fade_transition",
                    "message_format",
                    "message_offline",
                    "replay_gain_enabled",
                    "replay_gain_offset",
                },
            ),
        )


@final
class StreamStateView(views.APIView):

    serializer_class: type[Serializer[Any]] = StreamStateSerializer
    permission_classes: PermissionsType = (IsSystemTokenOrUser,)
    model_permission_name: str = "streamsetting"

    def get(self, _: Request) -> Response:
        data = Preference.get_stream_state()
        return Response(
            data.model_dump(
                include={
                    "input_main_connected",
                    "input_main_streaming",
                    "input_show_connected",
                    "input_show_streaming",
                    "schedule_streaming",
                },
            ),
        )
