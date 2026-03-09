from rest_framework import serializers

from api.core.models import ServiceRegister


class ServiceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRegister
        fields = "__all__"
