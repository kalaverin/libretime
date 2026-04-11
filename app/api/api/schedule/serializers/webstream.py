from datetime import timedelta
from typing import Any, final

from django.db.models import Model

from api.schedule.models import Webstream, WebstreamMetadata
from api.serializers import SecureModelSerializer
from api.validators.url import validate_url_not_internal
from api.validators.xss import validate_no_xss


@final
class WebstreamSerializer(SecureModelSerializer):

    class Meta:
        model: type[Model] = Webstream
        fields: str = "__all__"
        extra_kwargs = {
            "length": {"required": False},
            "url": {"validators": [validate_url_not_internal]},
        }

    def create(self, validated_data: dict[str, Any]) -> Webstream:
        """Create webstream with default values for optional fields."""
        # Set default for length
        validated_data.setdefault("length", timedelta(seconds=0))

        # SecureModelSerializer handles created_at/updated_at
        return super().create(validated_data)

    def validate_name(self, value: str) -> str:
        """Validate name field for XSS."""
        if value:
            validate_no_xss(value)
        return value

    def validate_description(self, value: str) -> str:
        """Validate description field for XSS."""
        if value:
            validate_no_xss(value)
        return value

    def validate_mime(self, value: str) -> str:
        """Validate MIME type field for XSS."""
        if value:
            validate_no_xss(value)
        return value


@final
class WebstreamMetadataSerializer(SecureModelSerializer):

    class Meta:
        model: type[Model] = WebstreamMetadata
        fields: str = "__all__"
