"""
URL Configuration

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from api.core.router import urls as core_urls
from api.history.router import urls as history_urls
from api.podcasts.router import urls as podcasts_urls
from api.schedule.router import urls as schedule_urls
from api.storage.router import urls as storage_urls

api_urls = (
    *core_urls,
    *history_urls,
    *podcasts_urls,
    *schedule_urls,
    *storage_urls,
)

urlpatterns = [
    path(
        "api/browser/",
        include("rest_framework.urls", namespace="rest_framework"),
    ),
    path("api/v2/", include(list(api_urls))),
    path(
        "api/v2/schema",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "api/v2/schema/swagger-ui",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
