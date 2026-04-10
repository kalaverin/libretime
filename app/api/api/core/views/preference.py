from typing import Any, final

from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from api.core.models import Preference
from api.core.serializers import PreferenceSerializer


@final
class PreferenceViewSet(viewsets.ModelViewSet[Any]):

    queryset = Preference.objects.all()
    serializer_class: type[Serializer[Any]] = PreferenceSerializer
    model_permission_name: str = "preference"

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """Create preference with proper error handling for duplicate keys.

        The database has a unique constraint on the key field (cc_pref_key_idx),
        which may conflict with the intended unique_together = (user, key) behavior.
        We catch IntegrityError and return 400 instead of 500.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except IntegrityError as exc:
            # Handle database-level unique constraint violation
            error_msg = str(exc)
            if "cc_pref_key_idx" in error_msg or "unique" in error_msg.lower():
                return Response(
                    {"key": ["Preference with this key already exists."]},
                    status=HTTP_400_BAD_REQUEST,
                )
            raise

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=HTTP_201_CREATED, headers=headers,
        )
