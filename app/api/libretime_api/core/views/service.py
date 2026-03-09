from rest_framework import viewsets

from libretime_api.core.models import ServiceRegister
from libretime_api.core.serializers import ServiceRegisterSerializer


class ServiceRegisterViewSet(viewsets.ModelViewSet):
    queryset = ServiceRegister.objects.all()
    serializer_class = ServiceRegisterSerializer
    model_permission_name = "serviceregister"
