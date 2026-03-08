from rest_framework import viewsets

from libretime_api.core.models import Preference
from libretime_api.core.serializers import PreferenceSerializer


class PreferenceViewSet(viewsets.ModelViewSet):
    queryset = Preference.objects.all()
    serializer_class = PreferenceSerializer
    model_permission_name = "preference"
