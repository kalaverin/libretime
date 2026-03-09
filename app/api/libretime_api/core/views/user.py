from django.contrib.auth import get_user_model
from rest_framework import viewsets

from libretime_api.core.serializers import UserSerializer
from libretime_api.permissions import IsAdminOrOwnUser


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrOwnUser]
    model_permission_name = "user"
