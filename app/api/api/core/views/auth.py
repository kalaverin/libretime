from typing import Any, final

from rest_framework import viewsets
from rest_framework.serializers import Serializer

from api.core.models import LoginAttempt, UserToken
from api.core.serializers import (
    LoginAttemptSerializer,
    UserTokenSerializer,
)


@final
class UserTokenViewSet(viewsets.ModelViewSet[Any]):

    queryset = UserToken.objects.all()
    serializer_class: type[Serializer[Any]] = UserTokenSerializer
    model_permission_name: str = "usertoken"


@final
class LoginAttemptViewSet(viewsets.ModelViewSet[Any]):

    queryset = LoginAttempt.objects.all()
    serializer_class: type[Serializer[Any]] = LoginAttemptSerializer
    model_permission_name: str = "loginattempt"
