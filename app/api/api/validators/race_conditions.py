"""Race condition protection validators.

These validators help prevent race conditions in concurrent operations
by checking for duplicates and validating constraints at the application level.
"""

from typing import Any

from django.db import transaction
from django.db.models import Model, Q
from rest_framework.serializers import ValidationError


def validate_duplicate_name(
    model_class: type[Model],
    name: str,
    owner_id: int,
    exclude_id: int | None = None,
    field_name: str = "name",
) -> None:
    """Validate that name is unique per owner (T433, T539).

    Args:
        model_class: The model class to check
        name: The name to validate
        owner_id: The owner ID to scope uniqueness
        exclude_id: Optional ID to exclude (for updates)
        field_name: The field name for error messages
    """
    queryset = model_class.objects.filter(
        name=name,
        owner_id=owner_id,
    )
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        raise ValidationError(
            {field_name: f"A {model_class.__name__} with this name already exists."},
            code=f"{field_name}_duplicate",
        )


def validate_duplicate_url(
    model_class: type[Model],
    url: str,
    owner_id: int | None = None,
    exclude_id: int | None = None,
    field_name: str = "url",
) -> None:
    """Validate that URL is unique.

    Args:
        model_class: The model class to check
        url: The URL to validate
        owner_id: Optional owner ID to scope uniqueness
        exclude_id: Optional ID to exclude (for updates)
        field_name: The field name for error messages
    """
    queryset = model_class.objects.filter(url=url)
    if owner_id:
        queryset = queryset.filter(owner_id=owner_id)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        raise ValidationError(
            {field_name: f"A {model_class.__name__} with this URL already exists."},
            code=f"{field_name}_duplicate",
        )


def validate_duplicate_combination(
    model_class: type[Model],
    filters: dict[str, Any],
    exclude_id: int | None = None,
    error_message: str | None = None,
) -> None:
    """Validate that a combination of fields is unique (T486, T504).

    Args:
        model_class: The model class to check
        filters: Dict of field names to values
        exclude_id: Optional ID to exclude (for updates)
        error_message: Custom error message
    """
    queryset = model_class.objects.filter(**filters)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        msg = error_message or f"A {model_class.__name__} with these values already exists."
        raise ValidationError(msg, code="duplicate_combination")


def get_or_create_with_lock(
    model_class: type[Model],
    defaults: dict[str, Any] | None = None,
    **kwargs: Any,
) -> tuple[Model, bool]:
    """Get or create with select_for_update to prevent race conditions.

    Args:
        model_class: The model class
        defaults: Default values for creation
        **kwargs: Lookup parameters

    Returns:
        Tuple of (instance, created)
    """
    with transaction.atomic():
        try:
            # Try to get existing with lock
            instance = model_class.objects.select_for_update().get(**kwargs)
            return instance, False
        except model_class.DoesNotExist:
            # Create new instance
            create_kwargs = {**kwargs, **(defaults or {})}
            instance = model_class.objects.create(**create_kwargs)
            return instance, True


def validate_concurrent_update(
    model_class: type[Model],
    instance_id: int,
    expected_version: str | None = None,
    version_field: str = "updated_at",
) -> Model:
    """Validate that instance hasn't been modified by concurrent update (T555).

    Args:
        model_class: The model class
        instance_id: The instance ID
        expected_version: The expected version/timestamp
        version_field: The field to check for version

    Returns:
        The locked instance

    Raises:
        ValidationError: If instance was modified or not found
    """
    with transaction.atomic():
        try:
            instance = model_class.objects.select_for_update().get(id=instance_id)
        except model_class.DoesNotExist:
            raise ValidationError(
                f"{model_class.__name__} not found.",
                code="not_found",
            )

        if expected_version and hasattr(instance, version_field):
            current_version = getattr(instance, version_field)
            if str(current_version) != str(expected_version):
                raise ValidationError(
                    "This record was modified by another user. Please refresh and try again.",
                    code="concurrent_modification",
                )

        return instance
