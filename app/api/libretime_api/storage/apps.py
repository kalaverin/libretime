from django.apps import AppConfig


class StorageConfig(AppConfig):

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "libretime_api.storage"
    verbose_name: str = "LibreTime Storage API"
