from typing import Any, final

from django.db.models import Model
from rest_framework.serializers import ModelSerializer, ValidationError

from api.schedule.models import Playlist, PlaylistContent


@final
class PlaylistSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = Playlist
        fields: str = "__all__"


@final
class PlaylistContentSerializer(ModelSerializer[Any]):

    class Meta:
        model: type[Model] = PlaylistContent
        fields: str = "__all__"
        extra_kwargs = {
            "playlist": {"required": True},
        }

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate that FILE kind has file assigned."""
        kind = data.get("kind")
        file_obj = data.get("file")

        if kind == PlaylistContent.Kind.FILE and not file_obj:
            raise ValidationError(
                {"file": "File is required when kind is FILE."}
            )

        return data
