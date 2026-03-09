from typing import Any, final

from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.core.serializers import UserSerializer
from api.permissions import IsAdminOrOwnUser, PermissionsType


@final
class UserViewSet(viewsets.ModelViewSet[Any]):

    queryset = get_user_model().objects.all()
    serializer_class: type[Serializer[Any]] = UserSerializer
    permission_classes: PermissionsType = (IsAdminOrOwnUser,)
    model_permission_name: str = "user"
