from django.apps import AppConfig
from typing_extensions import final


@final
class StorageConfig(AppConfig):

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "api.storage"
    verbose_name: str = "LibreTime Storage API"
