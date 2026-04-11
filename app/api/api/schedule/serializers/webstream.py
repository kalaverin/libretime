from datetime import timedelta
from typing import Any, final

from django.db.models import Model

from api.schedule.models import Webstream, WebstreamMetadata
from api.serializers import SecureModelSerializer
from api.validators.race_conditions import (
    validate_concurrent_update,
    validate_duplicate_name,
    validate_duplicate_url,
)
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

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate duplicate name (T539) and URL (T539)."""
        name = data.get("name")
        url = data.get("url")
        owner = data.get("owner")
        
        # Get owner ID for validation
        if self.instance:
            owner_id = owner.id if owner else self.instance.owner_id
        else:
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                owner_id = request.user.id
            else:
                owner_id = None
        
        # T539: Check for duplicate name
        if name and owner_id:
            validate_duplicate_name(
                Webstream,
                name,
                owner_id,
                exclude_id=self.instance.id if self.instance else None,
            )
        
        # T539: Check for duplicate URL
        if url and owner_id:
            validate_duplicate_url(
                Webstream,
                url,
                owner_id,
                exclude_id=self.instance.id if self.instance else None,
            )
        
        return super().validate(data)


@final
class WebstreamMetadataSerializer(SecureModelSerializer):

    class Meta:
        model: type[Model] = WebstreamMetadata
        fields: str = "__all__"
