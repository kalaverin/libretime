"""Unit tests for API schedule models."""

from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.db.models import DO_NOTHING
from django.utils.timezone import now

from api.schedule.models.playlist import Playlist, PlaylistContent
from api.schedule.models.schedule import Schedule
from api.schedule.models.show import (
    Record,
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)


class TestPlaylist:
    """Tests for Playlist model."""

    @pytest.fixture
    def playlist(self, mocker):
        """Create a test playlist instance."""
        mock_owner = mocker.Mock()
        return Playlist(
            id=1,
            name="Test Playlist",
            description="A test playlist",
            length=timedelta(hours=1),
            owner=mock_owner,
        )

    def test_meta_attributes(self):
        """Test Playlist model Meta attributes."""
        assert Playlist._meta.managed is False
        assert Playlist._meta.db_table == "cc_playlist"

    def test_field_definitions(self):
        """Test Playlist model field definitions."""
        # Test name field
        name_field = Playlist._meta.get_field("name")
        assert name_field.max_length == 255
        
        # Test description field
        description_field = Playlist._meta.get_field("description")
        assert description_field.max_length == 512
        assert description_field.blank is True
        assert description_field.null is True
        
        # Test length field
        length_field = Playlist._meta.get_field("length")
        assert length_field.get_internal_type() == "DurationField"
        assert length_field.blank is True
        assert length_field.null is True
        
        # Test created_at with db_column
        created_at_field = Playlist._meta.get_field("created_at")
        assert created_at_field.get_internal_type() == "DateTimeField"
        assert created_at_field.db_column == "utime"
        assert created_at_field.blank is True
        assert created_at_field.null is True
        
        # Test updated_at with db_column
        updated_at_field = Playlist._meta.get_field("updated_at")
        assert updated_at_field.get_internal_type() == "DateTimeField"
        assert updated_at_field.db_column == "mtime"
        assert updated_at_field.blank is True
        assert updated_at_field.null is True
        
        # Test owner foreign key with db_column
        owner_field = Playlist._meta.get_field("owner")
        assert owner_field.remote_field.model._meta.app_label == "core"
        assert owner_field.remote_field.model.__name__ == "User"
        assert owner_field.db_column == "creator_id"
        assert owner_field.remote_field.on_delete == DO_NOTHING
        assert owner_field.blank is True
        assert owner_field.null is True

    def test_get_owner(self, playlist):
        """Test get_owner returns the playlist owner."""
        owner = playlist.get_owner()
        
        assert owner == playlist.owner

    def test_get_owner_none(self):
        """Test get_owner returns None when no owner."""
        playlist_no_owner = Playlist(
            name="Orphan Playlist",
            owner=None,
        )
        
        owner = playlist_no_owner.get_owner()
        
        assert owner is None


class TestPlaylistContent:
    """Tests for PlaylistContent model."""

    @pytest.fixture
    def playlist_content(self, mocker):
        """Create a test playlist content instance."""
        mock_playlist = mocker.Mock()
        mock_playlist.get_owner.return_value = mocker.Mock()
        mock_file = mocker.Mock()
        
        return PlaylistContent(
            id=1,
            playlist=mock_playlist,
            kind=PlaylistContent.Kind.FILE,
            file=mock_file,
            position=1,
            offset=0.0,
            length=timedelta(minutes=3),
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=3),
        )

    def test_meta_attributes(self):
        """Test PlaylistContent model Meta attributes."""
        assert PlaylistContent._meta.managed is False
        assert PlaylistContent._meta.db_table == "cc_playlistcontents"

    def test_kind_choices(self):
        """Test Kind choices."""
        assert PlaylistContent.Kind.FILE == 0
        assert PlaylistContent.Kind.STREAM == 1
        assert PlaylistContent.Kind.BLOCK == 2
        
        assert PlaylistContent.Kind.choices == [
            (0, "File"),
            (1, "Stream"),
            (2, "Block"),
        ]

    def test_field_definitions(self):
        """Test PlaylistContent model field definitions."""
        # Test kind field with db_column
        kind_field = PlaylistContent._meta.get_field("kind")
        assert kind_field.get_internal_type() == "SmallIntegerField"
        assert kind_field.db_column == "type"
        
        # Test position field
        position_field = PlaylistContent._meta.get_field("position")
        assert position_field.get_internal_type() == "IntegerField"
        assert position_field.blank is True
        assert position_field.null is True
        
        # Test offset field with db_column
        offset_field = PlaylistContent._meta.get_field("offset")
        assert offset_field.get_internal_type() == "FloatField"
        assert offset_field.db_column == "trackoffset"
        
        # Test length field with db_column
        length_field = PlaylistContent._meta.get_field("length")
        assert length_field.get_internal_type() == "DurationField"
        assert length_field.db_column == "cliplength"
        assert length_field.blank is True
        assert length_field.null is True
        
        # Test cue_in field with db_column
        cue_in_field = PlaylistContent._meta.get_field("cue_in")
        assert cue_in_field.get_internal_type() == "DurationField"
        assert cue_in_field.db_column == "cuein"
        assert cue_in_field.blank is True
        assert cue_in_field.null is True
        
        # Test cue_out field with db_column
        cue_out_field = PlaylistContent._meta.get_field("cue_out")
        assert cue_out_field.get_internal_type() == "DurationField"
        assert cue_out_field.db_column == "cueout"
        assert cue_out_field.blank is True
        assert cue_out_field.null is True
        
        # Test fade_in field with db_column
        fade_in_field = PlaylistContent._meta.get_field("fade_in")
        assert fade_in_field.get_internal_type() == "TimeField"
        assert fade_in_field.db_column == "fadein"
        assert fade_in_field.blank is True
        assert fade_in_field.null is True
        
        # Test fade_out field with db_column
        fade_out_field = PlaylistContent._meta.get_field("fade_out")
        assert fade_out_field.get_internal_type() == "TimeField"
        assert fade_out_field.db_column == "fadeout"
        assert fade_out_field.blank is True
        assert fade_out_field.null is True

    def test_foreign_keys(self):
        """Test PlaylistContent foreign key definitions."""
        # Test playlist foreign key
        playlist_field = PlaylistContent._meta.get_field("playlist")
        assert playlist_field.remote_field.model._meta.app_label == "schedule"
        assert playlist_field.remote_field.model.__name__ == "Playlist"
        assert playlist_field.remote_field.on_delete == DO_NOTHING
        assert playlist_field.blank is True
        assert playlist_field.null is True
        
        # Test file foreign key
        file_field = PlaylistContent._meta.get_field("file")
        assert file_field.remote_field.model._meta.app_label == "storage"
        assert file_field.remote_field.model.__name__ == "File"
        assert file_field.remote_field.on_delete == DO_NOTHING
        assert file_field.blank is True
        assert file_field.null is True
        
        # Test stream foreign key
        stream_field = PlaylistContent._meta.get_field("stream")
        assert stream_field.remote_field.model._meta.app_label == "schedule"
        assert stream_field.remote_field.model.__name__ == "Webstream"
        assert stream_field.remote_field.on_delete == DO_NOTHING
        assert stream_field.blank is True
        assert stream_field.null is True
        
        # Test block foreign key
        block_field = PlaylistContent._meta.get_field("block")
        assert block_field.remote_field.model._meta.app_label == "schedule"
        assert block_field.remote_field.model.__name__ == "SmartBlock"
        assert block_field.remote_field.on_delete == DO_NOTHING
        assert block_field.blank is True
        assert block_field.null is True

    def test_get_owner(self, playlist_content):
        """Test get_owner returns owner's playlist's owner."""
        owner = playlist_content.get_owner()
        
        playlist_content.playlist.get_owner.assert_called_once()
        assert owner == playlist_content.playlist.get_owner.return_value

    def test_get_owner_with_none_playlist(self, mocker):
        """Test get_owner when playlist is None - raises AttributeError."""
        content = PlaylistContent(
            kind=PlaylistContent.Kind.FILE,
            playlist=None,
        )
        
        # BUG: This will raise AttributeError when trying to call get_owner on None
        with pytest.raises(AttributeError):
            content.get_owner()


class TestShow:
    """Tests for Show model."""

    @pytest.fixture
    def show(self, mocker):
        """Create a test show instance."""
        mock_hosts = mocker.MagicMock()
        mock_hosts.all.return_value = [mocker.Mock(), mocker.Mock()]
        
        show = Show(
            id=1,
            name="Test Show",
            description="A test show description",
            genre="Talk",
            url="https://example.com/show",
            image="/path/to/image.png",
            foreground_color="FFFFFF",
            background_color="000000",
            live_auth_registered=False,
            live_auth_custom=False,
            linked=True,
            linkable=True,
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
        show.hosts = mock_hosts
        return show

    @pytest.fixture
    def show_live_enabled(self, mocker):
        """Create a test show with live streaming enabled."""
        mock_hosts = mocker.MagicMock()
        mock_hosts.all.return_value = [mocker.Mock()]
        
        show = Show(
            id=2,
            name="Live Show",
            live_auth_registered=True,
            live_auth_custom=False,
            linked=False,
            linkable=False,
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
        show.hosts = mock_hosts
        return show

    def test_meta_attributes(self):
        """Test Show model Meta attributes."""
        assert Show._meta.managed is False
        assert Show._meta.db_table == "cc_show"

    def test_field_definitions_basic(self):
        """Test Show model basic field definitions."""
        # Test name field
        name_field = Show._meta.get_field("name")
        assert name_field.max_length == 255
        
        # Test description field
        description_field = Show._meta.get_field("description")
        assert description_field.max_length == 8192
        assert description_field.blank is True
        assert description_field.null is True
        
        # Test genre field
        genre_field = Show._meta.get_field("genre")
        assert genre_field.max_length == 255
        assert genre_field.blank is True
        assert genre_field.null is True
        
        # Test url field
        url_field = Show._meta.get_field("url")
        assert url_field.max_length == 255
        assert url_field.blank is True
        assert url_field.null is True

    def test_field_definitions_colors(self):
        """Test Show model color field definitions."""
        # Test image field with db_column
        image_field = Show._meta.get_field("image")
        assert image_field.max_length == 255
        assert image_field.db_column == "image_path"
        assert image_field.blank is True
        assert image_field.null is True
        
        # Test foreground_color field with db_column
        foreground_color_field = Show._meta.get_field("foreground_color")
        assert foreground_color_field.max_length == 6
        assert foreground_color_field.db_column == "color"
        assert foreground_color_field.blank is True
        assert foreground_color_field.null is True
        
        # Test background_color field
        background_color_field = Show._meta.get_field("background_color")
        assert background_color_field.max_length == 6
        assert background_color_field.blank is True
        assert background_color_field.null is True

    def test_field_definitions_live_auth(self):
        """Test Show model live auth field definitions."""
        # Test live_auth_registered with db_column
        live_auth_registered_field = Show._meta.get_field("live_auth_registered")
        assert live_auth_registered_field.get_internal_type() == "BooleanField"
        assert live_auth_registered_field.db_column == "live_stream_using_airtime_auth"
        assert live_auth_registered_field.default is False
        assert live_auth_registered_field.blank is True
        assert live_auth_registered_field.null is True
        
        # Test live_auth_custom with db_column
        live_auth_custom_field = Show._meta.get_field("live_auth_custom")
        assert live_auth_custom_field.get_internal_type() == "BooleanField"
        assert live_auth_custom_field.db_column == "live_stream_using_custom_auth"
        assert live_auth_custom_field.default is False
        assert live_auth_custom_field.blank is True
        assert live_auth_custom_field.null is True
        
        # Test live_auth_custom_user with db_column
        live_auth_custom_user_field = Show._meta.get_field("live_auth_custom_user")
        assert live_auth_custom_user_field.max_length == 255
        assert live_auth_custom_user_field.db_column == "live_stream_user"
        assert live_auth_custom_user_field.blank is True
        assert live_auth_custom_user_field.null is True
        
        # Test live_auth_custom_password with db_column
        live_auth_custom_password_field = Show._meta.get_field("live_auth_custom_password")
        assert live_auth_custom_password_field.max_length == 255
        assert live_auth_custom_password_field.db_column == "live_stream_pass"
        assert live_auth_custom_password_field.blank is True
        assert live_auth_custom_password_field.null is True

    def test_live_enabled_property_both_false(self, show):
        """Test live_enabled property when both auth methods are False."""
        assert show.live_enabled is False

    def test_live_enabled_property_registered(self, show_live_enabled):
        """Test live_enabled property when registered auth is enabled."""
        assert show_live_enabled.live_enabled is True

    def test_live_enabled_property_custom(self):
        """Test live_enabled property when custom auth is enabled."""
        show = Show(
            live_auth_registered=False,
            live_auth_custom=True,
            linked=False,
            linkable=False,
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
        
        assert show.live_enabled is True

    def test_live_enabled_property_both_true(self):
        """Test live_enabled property when both auth methods are enabled."""
        show = Show(
            live_auth_registered=True,
            live_auth_custom=True,
            linked=False,
            linkable=False,
            auto_playlist_enabled=False,
            auto_playlist_repeat=False,
            override_intro_playlist=False,
            override_outro_playlist=False,
        )
        
        assert show.live_enabled is True

    def test_field_definitions_linked(self):
        """Test Show model linked field definitions."""
        # Test linked field
        linked_field = Show._meta.get_field("linked")
        assert linked_field.get_internal_type() == "BooleanField"
        
        # Test linkable field with db_column
        linkable_field = Show._meta.get_field("linkable")
        assert linkable_field.get_internal_type() == "BooleanField"
        assert linkable_field.db_column == "is_linkable"

    def test_field_definitions_auto_playlist(self):
        """Test Show model auto playlist field definitions."""
        # Test auto_playlist foreign key with db_column
        auto_playlist_field = Show._meta.get_field("auto_playlist")
        assert auto_playlist_field.remote_field.model._meta.app_label == "schedule"
        assert auto_playlist_field.remote_field.model.__name__ == "Playlist"
        assert auto_playlist_field.db_column == "autoplaylist_id"
        assert auto_playlist_field.remote_field.on_delete == DO_NOTHING
        assert auto_playlist_field.blank is True
        assert auto_playlist_field.null is True
        
        # Test auto_playlist_enabled with db_column
        auto_playlist_enabled_field = Show._meta.get_field("auto_playlist_enabled")
        assert auto_playlist_enabled_field.get_internal_type() == "BooleanField"
        assert auto_playlist_enabled_field.db_column == "has_autoplaylist"
        
        # Test auto_playlist_repeat with db_column
        auto_playlist_repeat_field = Show._meta.get_field("auto_playlist_repeat")
        assert auto_playlist_repeat_field.get_internal_type() == "BooleanField"
        assert auto_playlist_repeat_field.db_column == "autoplaylist_repeat"

    def test_field_definitions_intro_outro(self):
        """Test Show model intro/outro playlist field definitions."""
        # Test intro_playlist foreign key with db_column and related_name
        intro_playlist_field = Show._meta.get_field("intro_playlist")
        assert intro_playlist_field.remote_field.model._meta.app_label == "schedule"
        assert intro_playlist_field.remote_field.model.__name__ == "Playlist"
        assert intro_playlist_field.db_column == "intro_playlist_id"
        assert intro_playlist_field.remote_field.related_name == "intro_playlist"
        assert intro_playlist_field.remote_field.on_delete == DO_NOTHING
        assert intro_playlist_field.blank is True
        assert intro_playlist_field.null is True
        
        # Test override_intro_playlist with db_column
        override_intro_field = Show._meta.get_field("override_intro_playlist")
        assert override_intro_field.get_internal_type() == "BooleanField"
        assert override_intro_field.db_column == "override_intro_playlist"
        
        # Test outro_playlist foreign key with db_column and related_name
        outro_playlist_field = Show._meta.get_field("outro_playlist")
        assert outro_playlist_field.remote_field.model._meta.app_label == "schedule"
        assert outro_playlist_field.remote_field.model.__name__ == "Playlist"
        assert outro_playlist_field.db_column == "outro_playlist_id"
        assert outro_playlist_field.remote_field.related_name == "outro_playlist"
        assert outro_playlist_field.remote_field.on_delete == DO_NOTHING
        assert outro_playlist_field.blank is True
        assert outro_playlist_field.null is True
        
        # Test override_outro_playlist with db_column
        override_outro_field = Show._meta.get_field("override_outro_playlist")
        assert override_outro_field.get_internal_type() == "BooleanField"
        assert override_outro_field.db_column == "override_outro_playlist"

    def test_hosts_many_to_many(self):
        """Test Show model hosts ManyToMany field."""
        hosts_field = Show._meta.get_field("hosts")
        assert hosts_field.get_internal_type() == "ManyToManyField"
        assert hosts_field.remote_field.model._meta.app_label == "core"
        assert hosts_field.remote_field.model.__name__ == "User"
        assert hosts_field.remote_field.through._meta.db_table == "cc_show_hosts"

    def test_get_owner(self, show):
        """Test get_owner returns the show's hosts queryset."""
        owners = show.get_owner()
        
        show.hosts.all.assert_called_once()
        assert owners == show.hosts.all.return_value


class TestShowHost:
    """Tests for ShowHost model."""

    def test_meta_attributes(self):
        """Test ShowHost model Meta attributes."""
        assert ShowHost._meta.managed is False
        assert ShowHost._meta.db_table == "cc_show_hosts"

    def test_field_definitions(self):
        """Test ShowHost model field definitions."""
        # Test show foreign key
        show_field = ShowHost._meta.get_field("show")
        assert show_field.remote_field.model._meta.app_label == "schedule"
        assert show_field.remote_field.model.__name__ == "Show"
        assert show_field.remote_field.on_delete == DO_NOTHING
        
        # Test user foreign key with db_column
        user_field = ShowHost._meta.get_field("user")
        assert user_field.remote_field.model._meta.app_label == "core"
        assert user_field.remote_field.model.__name__ == "User"
        assert user_field.db_column == "subjs_id"
        assert user_field.remote_field.on_delete == DO_NOTHING


class TestRecord:
    """Tests for Record choices."""

    def test_record_choices(self):
        """Test Record choices values."""
        assert Record.NO == 0
        assert Record.YES == 1
        
        assert Record.choices == [
            (0, "No"),
            (1, "Yes"),
        ]


class TestShowDays:
    """Tests for ShowDays model."""

    @pytest.fixture
    def show_days(self, mocker):
        """Create a test show days instance."""
        mock_show = mocker.Mock()
        mock_show.get_owner.return_value = mocker.MagicMock()
        
        return ShowDays(
            id=1,
            show=mock_show,
            first_show_on=date(2024, 1, 1),
            last_show_on=date(2024, 12, 31),
            start_time=time(10, 0),
            timezone="UTC",
            duration="01:00:00",
            record_enabled=Record.NO,
            week_day=ShowDays.WeekDay.MONDAY,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )

    def test_meta_attributes(self):
        """Test ShowDays model Meta attributes."""
        assert ShowDays._meta.managed is False
        assert ShowDays._meta.db_table == "cc_show_days"

    def test_week_day_choices(self):
        """Test WeekDay choices."""
        assert ShowDays.WeekDay.MONDAY == 0
        assert ShowDays.WeekDay.TUESDAY == 1
        assert ShowDays.WeekDay.WEDNESDAY == 2
        assert ShowDays.WeekDay.THURSDAY == 3
        assert ShowDays.WeekDay.FRIDAY == 4
        assert ShowDays.WeekDay.SATURDAY == 5
        assert ShowDays.WeekDay.SUNDAY == 6
        
        assert ShowDays.WeekDay.choices == [
            (0, "Monday"),
            (1, "Tuesday"),
            (2, "Wednesday"),
            (3, "Thursday"),
            (4, "Friday"),
            (5, "Saturday"),
            (6, "Sunday"),
        ]

    def test_repeat_kind_choices(self):
        """Test RepeatKind choices."""
        assert ShowDays.RepeatKind.WEEKLY == 0
        assert ShowDays.RepeatKind.WEEKLY_2 == 1
        assert ShowDays.RepeatKind.MONTHLY == 2
        assert ShowDays.RepeatKind.WEEKLY_3 == 4
        assert ShowDays.RepeatKind.WEEKLY_4 == 5
        
        assert ShowDays.RepeatKind.choices == [
            (0, "Every week"),
            (1, "Every 2 weeks"),
            (4, "Every 3 weeks"),
            (5, "Every 4 weeks"),
            (2, "Every month"),
        ]

    def test_field_definitions(self):
        """Test ShowDays model field definitions."""
        # Test first_show_on with db_column
        first_show_field = ShowDays._meta.get_field("first_show_on")
        assert first_show_field.get_internal_type() == "DateField"
        assert first_show_field.db_column == "first_show"
        
        # Test last_show_on with db_column
        last_show_field = ShowDays._meta.get_field("last_show_on")
        assert last_show_field.get_internal_type() == "DateField"
        assert last_show_field.db_column == "last_show"
        assert last_show_field.blank is True
        assert last_show_field.null is True
        
        # Test start_time field
        start_time_field = ShowDays._meta.get_field("start_time")
        assert start_time_field.get_internal_type() == "TimeField"
        
        # Test timezone field
        timezone_field = ShowDays._meta.get_field("timezone")
        assert timezone_field.max_length == 1024
        
        # Test duration field
        duration_field = ShowDays._meta.get_field("duration")
        assert duration_field.max_length == 1024
        
        # Test record_enabled with db_column
        record_enabled_field = ShowDays._meta.get_field("record_enabled")
        assert record_enabled_field.get_internal_type() == "SmallIntegerField"
        assert record_enabled_field.db_column == "record"
        assert record_enabled_field.default == Record.NO
        assert record_enabled_field.blank is True
        assert record_enabled_field.null is True
        
        # Test week_day with db_column
        week_day_field = ShowDays._meta.get_field("week_day")
        assert week_day_field.get_internal_type() == "SmallIntegerField"
        assert week_day_field.db_column == "day"
        assert week_day_field.blank is True
        assert week_day_field.null is True
        
        # Test repeat_kind with db_column
        repeat_kind_field = ShowDays._meta.get_field("repeat_kind")
        assert repeat_kind_field.get_internal_type() == "SmallIntegerField"
        assert repeat_kind_field.db_column == "repeat_type"
        
        # Test repeat_next_on with db_column
        repeat_next_on_field = ShowDays._meta.get_field("repeat_next_on")
        assert repeat_next_on_field.get_internal_type() == "DateField"
        assert repeat_next_on_field.db_column == "next_pop_date"
        assert repeat_next_on_field.blank is True
        assert repeat_next_on_field.null is True

    def test_get_owner(self, show_days):
        """Test get_owner delegates to show's get_owner."""
        owner = show_days.get_owner()
        
        show_days.show.get_owner.assert_called_once()
        assert owner == show_days.show.get_owner.return_value


class TestShowInstance:
    """Tests for ShowInstance model."""

    @pytest.fixture
    def show_instance(self, mocker):
        """Create a test show instance."""
        mock_show = mocker.Mock()
        mock_show.get_owner.return_value = mocker.MagicMock()
        
        return ShowInstance(
            id=1,
            show=mock_show,
            starts_at=datetime(2024, 1, 15, 10, 0, 0),
            ends_at=datetime(2024, 1, 15, 11, 0, 0),
            filled_time=timedelta(minutes=45),
            modified=False,
            auto_playlist_built=False,
            record_enabled=Record.NO,
        )

    def test_meta_attributes(self):
        """Test ShowInstance model Meta attributes."""
        assert ShowInstance._meta.managed is False
        assert ShowInstance._meta.db_table == "cc_show_instances"

    def test_field_definitions(self):
        """Test ShowInstance model field definitions."""
        # Test created_at with db_column
        created_at_field = ShowInstance._meta.get_field("created_at")
        assert created_at_field.get_internal_type() == "DateTimeField"
        assert created_at_field.db_column == "created"
        
        # Test starts_at with db_column
        starts_at_field = ShowInstance._meta.get_field("starts_at")
        assert starts_at_field.get_internal_type() == "DateTimeField"
        assert starts_at_field.db_column == "starts"
        
        # Test ends_at with db_column
        ends_at_field = ShowInstance._meta.get_field("ends_at")
        assert ends_at_field.get_internal_type() == "DateTimeField"
        assert ends_at_field.db_column == "ends"
        
        # Test filled_time with db_column
        filled_time_field = ShowInstance._meta.get_field("filled_time")
        assert filled_time_field.get_internal_type() == "DurationField"
        assert filled_time_field.db_column == "time_filled"
        assert filled_time_field.blank is True
        assert filled_time_field.null is True
        
        # Test last_scheduled_at with db_column
        last_scheduled_field = ShowInstance._meta.get_field("last_scheduled_at")
        assert last_scheduled_field.get_internal_type() == "DateTimeField"
        assert last_scheduled_field.db_column == "last_scheduled"
        assert last_scheduled_field.blank is True
        assert last_scheduled_field.null is True
        
        # Test description field
        description_field = ShowInstance._meta.get_field("description")
        assert description_field.max_length == 8192
        assert description_field.blank is True
        assert description_field.null is True
        
        # Test modified with db_column
        modified_field = ShowInstance._meta.get_field("modified")
        assert modified_field.get_internal_type() == "BooleanField"
        assert modified_field.db_column == "modified_instance"
        
        # Test rebroadcast field
        rebroadcast_field = ShowInstance._meta.get_field("rebroadcast")
        assert rebroadcast_field.get_internal_type() == "SmallIntegerField"
        assert rebroadcast_field.blank is True
        assert rebroadcast_field.null is True
        
        # Test auto_playlist_built with db_column
        auto_playlist_built_field = ShowInstance._meta.get_field("auto_playlist_built")
        assert auto_playlist_built_field.get_internal_type() == "BooleanField"
        assert auto_playlist_built_field.db_column == "autoplaylist_built"
        
        # Test record_enabled with db_column
        record_enabled_field = ShowInstance._meta.get_field("record_enabled")
        assert record_enabled_field.get_internal_type() == "SmallIntegerField"
        assert record_enabled_field.db_column == "record"
        assert record_enabled_field.default == Record.NO
        assert record_enabled_field.blank is True
        assert record_enabled_field.null is True

    def test_foreign_keys(self):
        """Test ShowInstance foreign key definitions."""
        # Test show foreign key
        show_field = ShowInstance._meta.get_field("show")
        assert show_field.remote_field.model._meta.app_label == "schedule"
        assert show_field.remote_field.model.__name__ == "Show"
        assert show_field.remote_field.on_delete == DO_NOTHING
        
        # Test instance self-referential foreign key
        instance_field = ShowInstance._meta.get_field("instance")
        assert instance_field.remote_field.model == ShowInstance
        assert instance_field.remote_field.on_delete == DO_NOTHING
        assert instance_field.blank is True
        assert instance_field.null is True
        
        # Test record_file foreign key with db_column
        record_file_field = ShowInstance._meta.get_field("record_file")
        assert record_file_field.remote_field.model._meta.app_label == "storage"
        assert record_file_field.remote_field.model.__name__ == "File"
        assert record_file_field.db_column == "file_id"
        assert record_file_field.remote_field.on_delete == DO_NOTHING
        assert record_file_field.blank is True
        assert record_file_field.null is True

    def test_get_owner(self, show_instance):
        """Test get_owner delegates to show's get_owner."""
        owner = show_instance.get_owner()
        
        show_instance.show.get_owner.assert_called_once()
        assert owner == show_instance.show.get_owner.return_value


class TestShowRebroadcast:
    """Tests for ShowRebroadcast model."""

    @pytest.fixture
    def show_rebroadcast(self, mocker):
        """Create a test show rebroadcast instance."""
        mock_show = mocker.Mock()
        mock_show.get_owner.return_value = mocker.MagicMock()
        
        return ShowRebroadcast(
            id=1,
            show=mock_show,
            day_offset="1",
            start_time=time(14, 0),
        )

    def test_meta_attributes(self):
        """Test ShowRebroadcast model Meta attributes."""
        assert ShowRebroadcast._meta.managed is False
        assert ShowRebroadcast._meta.db_table == "cc_show_rebroadcast"

    def test_field_definitions(self):
        """Test ShowRebroadcast model field definitions."""
        # Test show foreign key
        show_field = ShowRebroadcast._meta.get_field("show")
        assert show_field.remote_field.model._meta.app_label == "schedule"
        assert show_field.remote_field.model.__name__ == "Show"
        assert show_field.remote_field.on_delete == DO_NOTHING
        
        # Test day_offset field
        day_offset_field = ShowRebroadcast._meta.get_field("day_offset")
        assert day_offset_field.max_length == 1024
        
        # Test start_time field
        start_time_field = ShowRebroadcast._meta.get_field("start_time")
        assert start_time_field.get_internal_type() == "TimeField"

    def test_get_owner(self, show_rebroadcast):
        """Test get_owner delegates to show's get_owner."""
        owner = show_rebroadcast.get_owner()
        
        show_rebroadcast.show.get_owner.assert_called_once()
        assert owner == show_rebroadcast.show.get_owner.return_value


class TestSchedule:
    """Tests for Schedule model."""

    @pytest.fixture
    def schedule_normal(self, mocker):
        """Create a test schedule instance (normal case)."""
        mock_instance = mocker.Mock()
        mock_instance.ends_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_instance.get_owner.return_value = mocker.Mock()
        
        return Schedule(
            id=1,
            starts_at=datetime(2024, 1, 15, 10, 0, 0),
            ends_at=datetime(2024, 1, 15, 10, 5, 0),
            instance=mock_instance,
            position=1,
            position_status=Schedule.PositionStatus.INSIDE,
            broadcasted=1,
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=5),
        )

    @pytest.fixture
    def schedule_overbooked(self, mocker):
        """Create an overbooked schedule instance."""
        mock_instance = mocker.Mock()
        mock_instance.ends_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_instance.get_owner.return_value = mocker.Mock()
        
        return Schedule(
            id=2,
            starts_at=datetime(2024, 1, 15, 11, 30, 0),  # After show ends
            ends_at=datetime(2024, 1, 15, 11, 35, 0),
            instance=mock_instance,
            position=2,
            position_status=Schedule.PositionStatus.OUTSIDE,
            broadcasted=1,
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=5),
        )

    @pytest.fixture
    def schedule_boundary(self, mocker):
        """Create a boundary schedule (starts before, ends after show)."""
        mock_instance = mocker.Mock()
        mock_instance.ends_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_instance.get_owner.return_value = mocker.Mock()
        
        return Schedule(
            id=3,
            starts_at=datetime(2024, 1, 15, 10, 55, 0),
            ends_at=datetime(2024, 1, 15, 11, 5, 0),  # Ends after show
            instance=mock_instance,
            position=3,
            position_status=Schedule.PositionStatus.BOUNDARY,
            broadcasted=1,
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=10),
        )

    def test_meta_attributes(self):
        """Test Schedule model Meta attributes."""
        assert Schedule._meta.managed is False
        assert Schedule._meta.db_table == "cc_schedule"
        
        # Test custom permissions
        permissions = Schedule._meta.permissions
        assert ("change_own_schedule", "Change the content on their shows") in permissions
        assert ("delete_own_schedule", "Delete the content on their shows") in permissions

    def test_position_status_choices(self):
        """Test PositionStatus choices."""
        assert Schedule.PositionStatus.FILLER == -1
        assert Schedule.PositionStatus.OUTSIDE == 0
        assert Schedule.PositionStatus.INSIDE == 1
        assert Schedule.PositionStatus.BOUNDARY == 2
        
        assert Schedule.PositionStatus.choices == [
            (-1, "Filler"),
            (0, "Outside"),
            (1, "Inside"),
            (2, "Boundary"),
        ]

    def test_field_definitions_basic(self):
        """Test Schedule model basic field definitions."""
        # Test starts_at with db_column
        starts_at_field = Schedule._meta.get_field("starts_at")
        assert starts_at_field.get_internal_type() == "DateTimeField"
        assert starts_at_field.db_column == "starts"
        
        # Test ends_at with db_column
        ends_at_field = Schedule._meta.get_field("ends_at")
        assert ends_at_field.get_internal_type() == "DateTimeField"
        assert ends_at_field.db_column == "ends"
        
        # Test length with db_column
        length_field = Schedule._meta.get_field("length")
        assert length_field.get_internal_type() == "DurationField"
        assert length_field.db_column == "clip_length"
        assert length_field.blank is True
        assert length_field.null is True

    def test_field_definitions_cues_and_fades(self):
        """Test Schedule model cue and fade field definitions."""
        # Test fade_in field
        fade_in_field = Schedule._meta.get_field("fade_in")
        assert fade_in_field.get_internal_type() == "TimeField"
        assert fade_in_field.blank is True
        assert fade_in_field.null is True
        
        # Test fade_out field
        fade_out_field = Schedule._meta.get_field("fade_out")
        assert fade_out_field.get_internal_type() == "TimeField"
        assert fade_out_field.blank is True
        assert fade_out_field.null is True
        
        # Test cue_in field
        cue_in_field = Schedule._meta.get_field("cue_in")
        assert cue_in_field.get_internal_type() == "DurationField"
        
        # Test cue_out field
        cue_out_field = Schedule._meta.get_field("cue_out")
        assert cue_out_field.get_internal_type() == "DurationField"

    def test_field_definitions_position(self):
        """Test Schedule model position field definitions."""
        # Test position field
        position_field = Schedule._meta.get_field("position")
        assert position_field.get_internal_type() == "IntegerField"
        
        # Test position_status with db_column
        position_status_field = Schedule._meta.get_field("position_status")
        assert position_status_field.get_internal_type() == "SmallIntegerField"
        assert position_status_field.db_column == "playout_status"
        assert position_status_field.default == Schedule.PositionStatus.INSIDE

    def test_field_definitions_status(self):
        """Test Schedule model status field definitions."""
        # Test broadcasted field
        broadcasted_field = Schedule._meta.get_field("broadcasted")
        assert broadcasted_field.get_internal_type() == "SmallIntegerField"
        
        # Test played with db_column
        played_field = Schedule._meta.get_field("played")
        assert played_field.get_internal_type() == "BooleanField"
        assert played_field.db_column == "media_item_played"
        assert played_field.blank is True
        assert played_field.null is True

    def test_foreign_keys(self):
        """Test Schedule foreign key definitions."""
        # Test instance foreign key
        instance_field = Schedule._meta.get_field("instance")
        assert instance_field.remote_field.model._meta.app_label == "schedule"
        assert instance_field.remote_field.model.__name__ == "ShowInstance"
        assert instance_field.remote_field.on_delete == DO_NOTHING
        
        # Test file foreign key
        file_field = Schedule._meta.get_field("file")
        assert file_field.remote_field.model._meta.app_label == "storage"
        assert file_field.remote_field.model.__name__ == "File"
        assert file_field.remote_field.on_delete == DO_NOTHING
        assert file_field.blank is True
        assert file_field.null is True
        
        # Test stream foreign key
        stream_field = Schedule._meta.get_field("stream")
        assert stream_field.remote_field.model._meta.app_label == "schedule"
        assert stream_field.remote_field.model.__name__ == "Webstream"
        assert stream_field.remote_field.on_delete == DO_NOTHING
        assert stream_field.blank is True
        assert stream_field.null is True

    def test_overbooked_property_normal(self, schedule_normal):
        """Test overbooked property when schedule ends before show."""
        assert schedule_normal.overbooked is False

    def test_overbooked_property_overbooked(self, schedule_overbooked):
        """Test overbooked property when schedule starts after show ends."""
        assert schedule_overbooked.overbooked is True

    def test_overbooked_property_boundary(self, schedule_boundary):
        """Test overbooked property when schedule spans show boundary."""
        # starts_at (10:55) < ends_at (11:00), so not overbooked
        assert schedule_boundary.overbooked is False

    def test_get_owner(self, schedule_normal):
        """Test get_owner delegates to instance's get_owner."""
        owner = schedule_normal.get_owner()
        
        schedule_normal.instance.get_owner.assert_called_once()
        assert owner == schedule_normal.instance.get_owner.return_value

    def test_get_cue_out_normal_case(self, schedule_normal):
        """Test get_cue_out returns stored cue_out when schedule ends before show."""
        cue_out = schedule_normal.get_cue_out()
        
        assert cue_out == schedule_normal.cue_out

    def test_get_cue_out_boundary_case(self, schedule_boundary):
        """Test get_cue_out returns adjusted cue_out when schedule exceeds show."""
        cue_out = schedule_boundary.get_cue_out()
        
        # Expected: 11:00 - 10:55 = 5 minutes
        expected_cue_out = timedelta(minutes=5)
        assert cue_out == expected_cue_out

    def test_get_cue_out_overbooked(self, schedule_overbooked):
        """Test get_cue_out returns stored cue_out when schedule starts after show."""
        cue_out = schedule_overbooked.get_cue_out()
        
        # Even though it won't be played, returns stored cue_out
        assert cue_out == schedule_overbooked.cue_out

    def test_get_ends_at_normal_case(self, schedule_normal):
        """Test get_ends_at returns scheduled ends_at when within show."""
        ends_at = schedule_normal.get_ends_at()
        
        assert ends_at == schedule_normal.ends_at

    def test_get_ends_at_boundary_case(self, schedule_boundary):
        """Test get_ends_at returns show ends when schedule exceeds show."""
        ends_at = schedule_boundary.get_ends_at()
        
        assert ends_at == schedule_boundary.instance.ends_at

    def test_get_ends_at_overbooked(self, schedule_overbooked):
        """Test get_ends_at returns show ends when schedule starts after show."""
        ends_at = schedule_overbooked.get_ends_at()
        
        # When starts_at >= instance.ends_at, returns instance.ends_at
        assert ends_at == schedule_overbooked.instance.ends_at

    def test_is_file_scheduled_in_the_future_true(self, mocker):
        """Test is_file_scheduled_in_the_future when file has future schedule."""
        mock_filter = mocker.MagicMock()
        mock_filter.count.return_value = 1
        mocker.patch.object(
            Schedule.objects, "filter", return_value=mock_filter
        )
        
        result = Schedule.is_file_scheduled_in_the_future("file123")
        
        assert result is True
        Schedule.objects.filter.assert_called_once_with(
            file_id="file123",
            ends_at__gt=now(),
        )

    def test_is_file_scheduled_in_the_future_false(self, mocker):
        """Test is_file_scheduled_in_the_future when file has no future schedule."""
        mock_filter = mocker.MagicMock()
        mock_filter.count.return_value = 0
        mocker.patch.object(
            Schedule.objects, "filter", return_value=mock_filter
        )
        
        result = Schedule.is_file_scheduled_in_the_future("file456")
        
        assert result is False

    def test_get_cue_out_exact_boundary(self, mocker):
        """Test get_cue_out when schedule ends exactly at show end."""
        mock_instance = mocker.Mock()
        mock_instance.ends_at = datetime(2024, 1, 15, 11, 0, 0)
        
        schedule = Schedule(
            starts_at=datetime(2024, 1, 15, 10, 50, 0),
            ends_at=datetime(2024, 1, 15, 11, 0, 0),  # Exactly at show end
            instance=mock_instance,
            cue_out=timedelta(minutes=10),
        )
        
        cue_out = schedule.get_cue_out()
        
        # When ends_at <= instance.ends_at, should return stored cue_out
        assert cue_out == timedelta(minutes=10)

    def test_get_cue_out_exact_start_boundary(self, mocker):
        """Test get_cue_out edge case when starts_at equals instance.ends_at."""
        mock_instance = mocker.Mock()
        mock_instance.ends_at = datetime(2024, 1, 15, 11, 0, 0)
        
        schedule = Schedule(
            starts_at=datetime(2024, 1, 15, 11, 0, 0),  # Exactly at show end
            ends_at=datetime(2024, 1, 15, 11, 5, 0),
            instance=mock_instance,
            cue_out=timedelta(minutes=5),
        )
        
        cue_out = schedule.get_cue_out()
        
        # starts_at < instance.ends_at is False, so returns stored cue_out
        assert cue_out == timedelta(minutes=5)
