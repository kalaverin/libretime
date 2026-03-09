from rest_framework import viewsets

from libretime_api.storage.models import Library
from libretime_api.storage.serializers import LibrarySerializer


class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer
    model_permission_name = "library"
