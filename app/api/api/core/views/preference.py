from rest_framework import viewsets

from api.core.models import Preference
from api.core.serializers import PreferenceSerializer


class PreferenceViewSet(viewsets.ModelViewSet):
    queryset = Preference.objects.all()
    serializer_class = PreferenceSerializer
    model_permission_name = "preference"
