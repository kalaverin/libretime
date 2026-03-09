from api.core.views.auth import LoginAttemptViewSet, UserTokenViewSet
from api.core.views.info import InfoView, VersionView
from api.core.views.preference import PreferenceViewSet
from api.core.views.service import ServiceRegisterViewSet
from api.core.views.stream import (
    StreamPreferencesView,
    StreamStateView,
)
from api.core.views.user import UserViewSet
from api.core.views.worker import (
    CeleryTaskViewSet,
    ThirdPartyTrackReferenceViewSet,
)
