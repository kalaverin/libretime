from structlog import get_logger
import os

from os import remove
from typing import Any, final

from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import filepath_to_uri
from django_filters import rest_framework as filters
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from typing_extensions import override

from api.schedule.models import Schedule
from api.storage.models import File
from api.storage.serializers import FileSerializer

logger = get_logger(__name__)


@final
class FileInUse(APIException):

    status_code: int = status.HTTP_409_CONFLICT
    default_detail: str = "The file is currently used"
    default_code: str = "file_in_use"


@final
class FileViewSet(viewsets.ModelViewSet[Any]):

    queryset = File.objects.all()
    serializer_class: type[serializers.ModelSerializer[Any]] = FileSerializer
    model_permission_name: str = "file"
    filter_backends: tuple[Any, ...] = (filters.DjangoFilterBackend,)
    filterset_fields: tuple[str, ...] = ("md5", "genre")

    @action(detail=True, methods=["GET"])
    def download(self, _: Request, __: Any = None) -> HttpResponse:
        instance: File = self.get_object()

        response = HttpResponse()
        # HTTP headers must be USASCII encoded, or Nginx might not find the
        # file and will return a 404.
        redirect_uri = filepath_to_uri(
            os.path.join("/api/_media", instance.filepath),
        )
        response["X-Accel-Redirect"] = redirect_uri
        return response

    @override
    def perform_destroy(self, instance: File) -> None:

        if Schedule.is_file_scheduled_in_the_future(file_id=instance.id):
            raise FileInUse("file is scheduled in the future")

        try:
            if instance.filepath is None:
                logger.warning(
                    "file does not have a filepath: %d",
                    instance.id,
                )
                return

            path = os.path.join(
                settings.CONFIG.storage.path,
                instance.filepath,
            )

            if not os.path.isfile(path):
                logger.warning(
                    "file does not exist in storage: %d",
                    instance.id,
                )
                return

            remove(path)

        except OSError as exception:
            raise APIException(
                "could not delete file from storage",
            ) from exception
