from rest_framework import views
from rest_framework.response import Response

from libretime_api.core.models import Preference
from libretime_api.core.serializers import (
    StreamPreferencesSerializer,
    StreamStateSerializer,
)
from libretime_api.permissions import IsSystemTokenOrUser

class StreamPreferencesView(views.APIView):
    permission_classes = [IsSystemTokenOrUser]
    serializer_class = StreamPreferencesSerializer
    model_permission_name = "streamsetting"

    def get(self, request):
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


class StreamStateView(views.APIView):
    permission_classes = [IsSystemTokenOrUser]
    serializer_class = StreamStateSerializer
    model_permission_name = "streamsetting"

    def get(self, request):
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
