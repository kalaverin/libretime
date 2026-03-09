from typing import Any, final

from rest_framework import serializers, viewsets

from api.storage.models import Library
from api.storage.serializers import LibrarySerializer


@final
class LibraryViewSet(viewsets.ModelViewSet[Any]):

    queryset = Library.objects.all()
    serializer_class: type[serializers.ModelSerializer[Any]] = (
        LibrarySerializer
    )
    model_permission_name: str = "library"
