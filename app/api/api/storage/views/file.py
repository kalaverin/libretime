import os
import re
from os import remove
from pathlib import Path
from typing import Any, final

from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import filepath_to_uri
from django_filters import rest_framework as filters
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from structlog import get_logger
from typing_extensions import override

from api.mixins import AutoAssignOwnerMixin
from api.permissions import check_authorization_header
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
class FileViewSet(AutoAssignOwnerMixin, viewsets.ModelViewSet[Any]):

    queryset = File.objects.all()
    serializer_class: type[serializers.ModelSerializer[Any]] = FileSerializer
    model_permission_name: str = "file"
    filter_backends: tuple[Any, ...] = (filters.DjangoFilterBackend,)
    filterset_fields: tuple[str, ...] = ("md5", "genre")

    @action(detail=True, methods=["GET"])
    def download(self, request: Request, **__: Any) -> HttpResponse:
        # API-Key auth (services) - allow
        if check_authorization_header(request):
            pass  # Service auth allowed
        else:
            # Session auth - require authenticated user
            user = request.user
            if not user.is_authenticated:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)

        instance: File = self.get_object()

        response = HttpResponse()
        # HTTP headers must be USASCII encoded, or Nginx might not find the
        # file and will return a 404.
        redirect_uri = filepath_to_uri(
            os.path.join("/api/_media", instance.filepath),
        )
        response["X-Accel-Redirect"] = redirect_uri
        return response

    def _resolve_and_validate_path(self, filepath: str) -> Path:
        """
        Resolve filepath to absolute path using pathlib and validate it's within storage.

        Args:
            filepath: The relative filepath from the File instance

        Returns:
            Path: Resolved absolute Path object

        Raises:
            APIException: If path escapes storage directory or is invalid
        """
        try:
            storage_root = Path(settings.CONFIG.storage.path).resolve()

            # Join storage root with filepath and resolve
            # resolve() removes .., ., and symlinks
            full_path = (storage_root / filepath).resolve()

            # Security check: ensure resolved path is within storage
            # Using Path.is_relative_to() or manual check
            try:
                # Python 3.9+ has is_relative_to()
                is_within = full_path.is_relative_to(storage_root)
            except AttributeError:
                # Fallback for older Python: check if path starts with storage root
                try:
                    full_path.relative_to(storage_root)
                    is_within = True
                except ValueError:
                    is_within = False

            if not is_within:
                logger.error(
                    "file path escapes storage directory: %s resolves to %s, "
                    "which is outside storage root %s",
                    filepath,
                    full_path,
                    storage_root,
                )
                raise APIException(
                    "filepath escapes storage directory",
                )

            return full_path

        except (OSError, ValueError) as exc:
            logger.error(
                "error resolving filepath %s: %s",
                filepath,
                str(exc),
            )
            raise APIException(
                "invalid filepath",
            ) from exc

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

            # Use pathlib to resolve and validate path (T8)
            resolved_path = self._resolve_and_validate_path(instance.filepath)

            # Convert to string for os.path.isfile check
            path_str = str(resolved_path)

            if not os.path.isfile(path_str):
                logger.warning(
                    "file does not exist in storage: %d (resolved to %s)",
                    instance.id,
                    path_str,
                )
                return

            remove(path_str)

        except OSError as exception:
            raise APIException(
                "could not delete file from storage",
            ) from exception
