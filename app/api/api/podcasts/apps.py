from django.apps import AppConfig


class PodcastsConfig(AppConfig):

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "api.podcasts"
    verbose_name: str = "LibreTime Podcasts API"
