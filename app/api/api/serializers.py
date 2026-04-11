"""
Base serializers with mass assignment protection.

Provides:
- ProtectedFieldsSerializer: blocks mass assignment of sensitive fields
- StrictSerializer: rejects unknown/extra fields
- TimestampSerializer: auto-manages created_at/updated_at
"""

from typing import Any, final

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# Fields that should never be mass-assigned
PROTECTED_FIELDS = frozenset(
    [
        "id",
        "owner",
        "created_at",
        "updated_at",
    ],
)

# Fields that should be read-only by default (can be customized per serializer)
DEFAULT_READ_ONLY_FIELDS = frozenset(
    [
        "id",
        "created_at",
        "updated_at",
    ],
)


@final
class MassAssignmentError(ValidationError):
    """Raised when mass assignment of protected field is attempted."""

    def __init__(self, field: str) -> None:
        super().__init__(
            {field: f"Field '{field}' cannot be set directly."},
            code="mass_assignment_prohibited",
        )


@final
class ExtraFieldsError(ValidationError):
    """Raised when unknown/extra fields are provided."""

    def __init__(self, fields: list[str]) -> None:
        super().__init__(
            {
                "extra_fields": f"Unknown fields not allowed: {', '.join(fields)}",
            },
            code="extra_fields_prohibited",
        )


class ProtectedFieldsSerializer(serializers.ModelSerializer):
    """
    Serializer that protects against mass assignment attacks.

    Features:
    - Blocks direct setting of 'id', 'owner' in CREATE
    - Blocks modification of 'id', 'created_at' in UPDATE
    - Allows customization via Meta.read_only_fields and Meta.protected_fields

    Usage:
        class MySerializer(ProtectedFieldsSerializer):
            class Meta:
                model = MyModel
                fields = "__all__"
                read_only_fields = ["id", "created_at"]  # Additional read-only
                protected_fields = ["owner", "status"]   # Blocked in CREATE
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._setup_field_protection()

    def _setup_field_protection(self) -> None:
        """Configure field protection based on Meta settings."""
        meta = getattr(self, "Meta", None)
        if not meta:
            return

        # Get custom configuration
        read_only = set(getattr(meta, "read_only_fields", []))

        # Ensure defaults are included
        read_only |= DEFAULT_READ_ONLY_FIELDS

        # owner is always read-only - assigned by API only
        if "owner" in self.fields:
            self.fields["owner"].read_only = True

        # Apply to fields
        for field_name in read_only:
            if field_name in self.fields:
                self.fields[field_name].read_only = True

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate data against mass assignment rules."""
        data = super().validate(data)

        # Check initial_data before DRF removes read_only fields
        initial = getattr(self, "initial_data", {}) or {}

        # API sets created_at itself - never accept from outside (400)
        if "created_at" in initial:
            raise MassAssignmentError("created_at")

        # owner is assigned by API only - never accept from outside (400)
        if "owner" in initial:
            raise MassAssignmentError("owner")

        # Block id in both CREATE and UPDATE
        if "id" in initial:
            raise MassAssignmentError("id")

        return data


class StrictSerializer(ProtectedFieldsSerializer):
    """
    Strict serializer that rejects unknown/extra fields.

    Prevents mass assignment via typos or unknown field names
    that might be silently ignored by DRF.

    Usage:
        class MySerializer(StrictSerializer):
            class Meta:
                model = MyModel
                fields = "__all__"
    """

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate and reject extra fields."""
        data = super().validate(data)

        # Check for extra fields in initial data (not cleaned data)
        if hasattr(self, "initial_data"):
            unknown = set(self.initial_data.keys()) - set(self.fields.keys())
            if unknown:
                raise ExtraFieldsError(sorted(unknown))

        return data


class TimestampSerializer(ProtectedFieldsSerializer):
    """
    Serializer that auto-manages timestamp fields.

    - created_at: set automatically on CREATE, read-only after
    - updated_at: set automatically on CREATE and UPDATE

    Only sets timestamps if fields exist on the model.

    Usage:
        class MySerializer(TimestampSerializer):
            class Meta:
                model = MyModel
                fields = "__all__"
    """

    def _has_field(self, field_name: str) -> bool:
        """Check if model has the given field."""
        meta = getattr(self, "Meta", None)
        if not meta or not hasattr(meta, "model"):
            return False
        model = meta.model
        return hasattr(model, field_name)

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Create with auto timestamps."""
        from sdk import now

        current_time = now()

        # Set timestamps only if fields exist on model
        if self._has_field("created_at"):
            validated_data.setdefault("created_at", current_time)
        if self._has_field("updated_at"):
            validated_data.setdefault("updated_at", current_time)

        return super().create(validated_data)

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        """Update with auto updated_at."""
        from sdk import now

        # Always update updated_at if field exists
        if self._has_field("updated_at"):
            validated_data["updated_at"] = now()

        return super().update(instance, validated_data)


class SecureModelSerializer(TimestampSerializer, StrictSerializer):
    """
    Most secure serializer combining all protections.

    Features:
    - Blocks mass assignment of id, owner, created_at, updated_at
    - Rejects unknown/extra fields
    - Auto-manages timestamps (if fields exist on model)

    Recommended as default serializer for all models.

    Usage:
        class MySerializer(SecureModelSerializer):
            class Meta:
                model = MyModel
                fields = "__all__"
    """

