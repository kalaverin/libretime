from rest_framework import viewsets

from libretime_api.history.models import LiveLog
from libretime_api.history.serializers import LiveLogSerializer

class LiveLogViewSet(viewsets.ModelViewSet):
    queryset = LiveLog.objects.all()
    serializer_class = LiveLogSerializer
    model_permission_name = "livelog"
