from django.apps import AppConfig


class ScheduleConfig(AppConfig):

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "api.schedule"
    verbose_name: str = "LibreTime Schedule API"
