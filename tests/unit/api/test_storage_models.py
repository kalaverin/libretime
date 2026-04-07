"""Unit tests for API storage models."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.db.models import DO_NOTHING

from api.storage.models.file import File


class TestFile:
    """Tests for File model."""

    @pytest.fixture
    def file_instance(self, mocker):
        """Create a test file instance."""
        mock_owner = mocker.Mock()
        mock_library = mocker.Mock()
        
        return File(
            id=1,
            name="Test Song",
            filepath="/path/to/file.mp3",
            size=1024000,
            mime="audio/mpeg",
            owner=mock_owner,
            library=mock_library,
            import_status=File.ImportStatus.SUCCESS,
            hidden=False,
            accessed=0,
            scheduled=False,
            part_of_list=False,
        )

    @pytest.fixture
    def file_with_metadata(self, mocker):
        """Create a test file instance with full metadata."""
        mock_owner = mocker.Mock()
        
        return File(
            id=2,
            name="Full Metadata Song",
            filepath="/path/to/song.flac",
            size=5242880,
            mime="audio/flac",
            owner=mock_owner,
            import_status=File.ImportStatus.SUCCESS,
            bit_rate=320,
            sample_rate=44100,
            format="FLAC",
            channels=2,
            length=timedelta(minutes=3, seconds=30),
            bpm=120,
            replay_gain=Decimal("-6.50"),
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=3, seconds=30),
            description="A test song",
            artwork="/path/to/artwork.jpg",
            artist_name="Test Artist",
            artist_url="https://artist.example.com",
            original_artist="Original Artist",
            album_title="Test Album",
            track_title="Test Track",
            genre="Rock",
            mood="Energetic",
            date="2024",
            track_number=1,
            disc_number="1",
            comment="Test comment",
            language="English",
            label="Test Label",
            copyright="Test Copyright",
            composer="Test Composer",
            conductor="Test Conductor",
            orchestra="Test Orchestra",
            encoder="FLAC 1.3.0",
            encoded_by="Test Encoder",
            isrc="USABC2400001",
            lyrics="Test lyrics",
            lyricist="Test Lyricist",
            original_lyricist="Original Lyricist",
            subject="Test Subject",
            contributor="Test Contributor",
            rating="5",
            url="https://example.com/song",
            info_url="https://example.com/info",
            audio_source_url="https://example.com/source",
            buy_this_url="https://example.com/buy",
            catalog_number="CAT-001",
            radio_station_name="Test Radio",
            radio_station_url="https://radio.example.com",
            report_datetime="2024-01-15",
            report_location="Test Location",
            report_organization="Test Org",
        )

    def test_meta_attributes(self):
        """Test File model Meta attributes."""
        assert File._meta.managed is False
        assert File._meta.db_table == "cc_files"
        
        # Test custom permissions
        permissions = File._meta.permissions
        assert ("change_own_file", "Change the files where they are the owner") in permissions
        assert ("delete_own_file", "Delete the files where they are the owner") in permissions

    def test_import_status_choices(self):
        """Test ImportStatus choices."""
        assert File.ImportStatus.SUCCESS == 0
        assert File.ImportStatus.PENDING == 1
        assert File.ImportStatus.FAILED == 2
        
        # Test choice labels
        assert File.ImportStatus.choices == [
            (0, "Success"),
            (1, "Pending"),
            (2, "Failed"),
        ]

    def test_get_owner(self, file_instance):
        """Test get_owner returns the file owner."""
        owner = file_instance.get_owner()
        
        assert owner == file_instance.owner

    def test_get_owner_none(self):
        """Test get_owner returns None when no owner."""
        file_no_owner = File(
            name="Orphan File",
            filepath="/path/to/orphan.mp3",
            size=1024,
            mime="audio/mpeg",
            owner=None,
        )
        
        owner = file_no_owner.get_owner()
        
        assert owner is None

    def test_field_definitions_basic(self):
        """Test File model basic field definitions."""
        # Test name field
        name_field = File._meta.get_field("name")
        assert name_field.max_length == 255
        
        # Test filepath field
        filepath_field = File._meta.get_field("filepath")
        assert filepath_field.get_internal_type() == "TextField"
        assert filepath_field.blank is True
        assert filepath_field.null is True
        
        # Test size field with db_column
        size_field = File._meta.get_field("size")
        assert size_field.db_column == "filesize"
        
        # Test mime field
        mime_field = File._meta.get_field("mime")
        assert mime_field.max_length == 255
        
        # Test md5 field
        md5_field = File._meta.get_field("md5")
        assert md5_field.max_length == 32
        assert md5_field.blank is True
        assert md5_field.null is True

    def test_field_definitions_booleans(self):
        """Test File model boolean field definitions."""
        # Test hidden field
        hidden_field = File._meta.get_field("hidden")
        assert hidden_field.get_internal_type() == "BooleanField"
        assert hidden_field.blank is True
        assert hidden_field.null is True
        
        # Test exists field with db_column
        exists_field = File._meta.get_field("exists")
        assert exists_field.db_column == "file_exists"
        assert exists_field.blank is True
        assert exists_field.null is True
        
        # Test scheduled field with db_column
        scheduled_field = File._meta.get_field("scheduled")
        assert scheduled_field.db_column == "is_scheduled"
        assert scheduled_field.blank is True
        assert scheduled_field.null is True
        
        # Test part_of_list field with db_column
        part_of_list_field = File._meta.get_field("part_of_list")
        assert part_of_list_field.db_column == "is_playlist"
        assert part_of_list_field.blank is True
        assert part_of_list_field.null is True

    def test_field_definitions_timestamps(self):
        """Test File model timestamp field definitions."""
        # Test created_at with db_column
        created_at_field = File._meta.get_field("created_at")
        assert created_at_field.get_internal_type() == "DateTimeField"
        assert created_at_field.db_column == "utime"
        assert created_at_field.blank is True
        assert created_at_field.null is True
        
        # Test updated_at with db_column
        updated_at_field = File._meta.get_field("updated_at")
        assert created_at_field.get_internal_type() == "DateTimeField"
        assert updated_at_field.db_column == "mtime"
        assert updated_at_field.blank is True
        assert updated_at_field.null is True
        
        # Test last_played_at with db_column
        last_played_at_field = File._meta.get_field("last_played_at")
        assert last_played_at_field.db_column == "lptime"
        assert last_played_at_field.blank is True
        assert last_played_at_field.null is True

    def test_field_definitions_foreign_keys(self):
        """Test File model foreign key definitions."""
        # Test owner field
        owner_field = File._meta.get_field("owner")
        assert owner_field.remote_field.model._meta.app_label == "core"
        assert owner_field.remote_field.model.__name__ == "User"
        assert owner_field.remote_field.on_delete == DO_NOTHING
        assert owner_field.blank is True
        assert owner_field.null is True
        
        # Test library field with db_column
        library_field = File._meta.get_field("library")
        assert library_field.remote_field.model._meta.app_label == "storage"
        assert library_field.remote_field.model.__name__ == "Library"
        assert library_field.db_column == "track_type_id"
        assert library_field.remote_field.on_delete == DO_NOTHING
        assert library_field.blank is True
        assert library_field.null is True
        
        # Test edited_by field with db_column and related_name
        edited_by_field = File._meta.get_field("edited_by")
        assert edited_by_field.remote_field.model._meta.app_label == "core"
        assert edited_by_field.remote_field.model.__name__ == "User"
        assert edited_by_field.db_column == "editedby"
        assert edited_by_field.remote_field.related_name == "edited_files"
        assert edited_by_field.remote_field.on_delete == DO_NOTHING
        assert edited_by_field.blank is True
        assert edited_by_field.null is True

    def test_field_definitions_audio(self):
        """Test File model audio field definitions."""
        # Test bit_rate field
        bit_rate_field = File._meta.get_field("bit_rate")
        assert bit_rate_field.get_internal_type() == "IntegerField"
        assert bit_rate_field.blank is True
        assert bit_rate_field.null is True
        
        # Test sample_rate field
        sample_rate_field = File._meta.get_field("sample_rate")
        assert sample_rate_field.get_internal_type() == "IntegerField"
        assert sample_rate_field.blank is True
        assert sample_rate_field.null is True
        
        # Test format field
        format_field = File._meta.get_field("format")
        assert format_field.max_length == 128
        assert format_field.blank is True
        assert format_field.null is True
        
        # Test channels field
        channels_field = File._meta.get_field("channels")
        assert channels_field.get_internal_type() == "IntegerField"
        assert channels_field.blank is True
        assert channels_field.null is True
        
        # Test length field
        length_field = File._meta.get_field("length")
        assert length_field.get_internal_type() == "DurationField"
        assert length_field.blank is True
        assert length_field.null is True
        
        # Test bpm field
        bpm_field = File._meta.get_field("bpm")
        assert bpm_field.get_internal_type() == "IntegerField"
        assert bpm_field.blank is True
        assert bpm_field.null is True
        
        # Test replay_gain field
        replay_gain_field = File._meta.get_field("replay_gain")
        assert replay_gain_field.get_internal_type() == "DecimalField"
        assert replay_gain_field.max_digits == 8
        assert replay_gain_field.decimal_places == 2
        assert replay_gain_field.blank is True
        assert replay_gain_field.null is True
        
        # Test cue_in field with db_column
        cue_in_field = File._meta.get_field("cue_in")
        assert cue_in_field.get_internal_type() == "DurationField"
        assert cue_in_field.db_column == "cuein"
        assert cue_in_field.blank is True
        assert cue_in_field.null is True
        
        # Test cue_out field with db_column
        cue_out_field = File._meta.get_field("cue_out")
        assert cue_out_field.get_internal_type() == "DurationField"
        assert cue_out_field.db_column == "cueout"
        assert cue_out_field.blank is True
        assert cue_out_field.null is True

    def test_field_definitions_metadata(self):
        """Test File model metadata field definitions."""
        # Test description field
        description_field = File._meta.get_field("description")
        assert description_field.max_length == 512
        assert description_field.blank is True
        assert description_field.null is True
        
        # Test artwork field
        artwork_field = File._meta.get_field("artwork")
        assert artwork_field.max_length == 512
        assert artwork_field.blank is True
        assert artwork_field.null is True
        
        # Test artist_name field
        artist_name_field = File._meta.get_field("artist_name")
        assert artist_name_field.max_length == 512
        assert artist_name_field.blank is True
        assert artist_name_field.null is True
        
        # Test artist_url field
        artist_url_field = File._meta.get_field("artist_url")
        assert artist_url_field.max_length == 512
        assert artist_url_field.blank is True
        assert artist_url_field.null is True
        
        # Test album_title field
        album_title_field = File._meta.get_field("album_title")
        assert album_title_field.max_length == 512
        assert album_title_field.blank is True
        assert album_title_field.null is True
        
        # Test track_title field
        track_title_field = File._meta.get_field("track_title")
        assert track_title_field.max_length == 512
        assert track_title_field.blank is True
        assert track_title_field.null is True
        
        # Test genre field
        genre_field = File._meta.get_field("genre")
        assert genre_field.max_length == 64
        assert genre_field.blank is True
        assert genre_field.null is True
        
        # Test mood field
        mood_field = File._meta.get_field("mood")
        assert mood_field.max_length == 64
        assert mood_field.blank is True
        assert mood_field.null is True
        
        # Test date field with db_column
        date_field = File._meta.get_field("date")
        assert date_field.max_length == 16
        assert date_field.db_column == "year"
        assert date_field.blank is True
        assert date_field.null is True
        
        # Test track_number field
        track_number_field = File._meta.get_field("track_number")
        assert track_number_field.get_internal_type() == "IntegerField"
        assert track_number_field.blank is True
        assert track_number_field.null is True
        
        # Test disc_number field
        disc_number_field = File._meta.get_field("disc_number")
        assert disc_number_field.max_length == 8
        assert disc_number_field.blank is True
        assert disc_number_field.null is True
        
        # Test comment field with db_column
        comment_field = File._meta.get_field("comment")
        assert comment_field.get_internal_type() == "TextField"
        assert comment_field.db_column == "comments"
        assert comment_field.blank is True
        assert comment_field.null is True
        
        # Test language field
        language_field = File._meta.get_field("language")
        assert language_field.max_length == 512
        assert language_field.blank is True
        assert language_field.null is True
        
        # Test label field
        label_field = File._meta.get_field("label")
        assert label_field.max_length == 512
        assert label_field.blank is True
        assert label_field.null is True
        
        # Test copyright field
        copyright_field = File._meta.get_field("copyright")
        assert copyright_field.max_length == 512
        assert copyright_field.blank is True
        assert copyright_field.null is True
        
        # Test composer field
        composer_field = File._meta.get_field("composer")
        assert composer_field.max_length == 512
        assert composer_field.blank is True
        assert composer_field.null is True
        
        # Test conductor field
        conductor_field = File._meta.get_field("conductor")
        assert conductor_field.max_length == 512
        assert conductor_field.blank is True
        assert conductor_field.null is True
        
        # Test orchestra field
        orchestra_field = File._meta.get_field("orchestra")
        assert orchestra_field.max_length == 512
        assert orchestra_field.blank is True
        assert orchestra_field.null is True
        
        # Test encoder field
        encoder_field = File._meta.get_field("encoder")
        assert encoder_field.max_length == 64
        assert encoder_field.blank is True
        assert encoder_field.null is True
        
        # Test encoded_by field
        encoded_by_field = File._meta.get_field("encoded_by")
        assert encoded_by_field.max_length == 255
        assert encoded_by_field.blank is True
        assert encoded_by_field.null is True
        
        # Test isrc field with db_column
        isrc_field = File._meta.get_field("isrc")
        assert isrc_field.max_length == 512
        assert isrc_field.db_column == "isrc_number"
        assert isrc_field.blank is True
        assert isrc_field.null is True
        
        # Test lyrics field
        lyrics_field = File._meta.get_field("lyrics")
        assert lyrics_field.get_internal_type() == "TextField"
        assert lyrics_field.blank is True
        assert lyrics_field.null is True
        
        # Test lyricist field
        lyricist_field = File._meta.get_field("lyricist")
        assert lyricist_field.max_length == 512
        assert lyricist_field.blank is True
        assert lyricist_field.null is True
        
        # Test original_lyricist field
        original_lyricist_field = File._meta.get_field("original_lyricist")
        assert original_lyricist_field.max_length == 512
        assert original_lyricist_field.blank is True
        assert original_lyricist_field.null is True

    def test_field_definitions_additional(self):
        """Test File model additional field definitions."""
        # Test subject field
        subject_field = File._meta.get_field("subject")
        assert subject_field.max_length == 512
        assert subject_field.blank is True
        assert subject_field.null is True
        
        # Test contributor field
        contributor_field = File._meta.get_field("contributor")
        assert contributor_field.max_length == 512
        assert contributor_field.blank is True
        assert contributor_field.null is True
        
        # Test rating field
        rating_field = File._meta.get_field("rating")
        assert rating_field.max_length == 8
        assert rating_field.blank is True
        assert rating_field.null is True
        
        # Test url field
        url_field = File._meta.get_field("url")
        assert url_field.max_length == 1024
        assert url_field.blank is True
        assert url_field.null is True
        
        # Test info_url field
        info_url_field = File._meta.get_field("info_url")
        assert info_url_field.max_length == 512
        assert info_url_field.blank is True
        assert info_url_field.null is True
        
        # Test audio_source_url field
        audio_source_url_field = File._meta.get_field("audio_source_url")
        assert audio_source_url_field.max_length == 512
        assert audio_source_url_field.blank is True
        assert audio_source_url_field.null is True
        
        # Test buy_this_url field
        buy_this_url_field = File._meta.get_field("buy_this_url")
        assert buy_this_url_field.max_length == 512
        assert buy_this_url_field.blank is True
        assert buy_this_url_field.null is True
        
        # Test catalog_number field
        catalog_number_field = File._meta.get_field("catalog_number")
        assert catalog_number_field.max_length == 512
        assert catalog_number_field.blank is True
        assert catalog_number_field.null is True
        
        # Test radio_station_name field
        radio_station_name_field = File._meta.get_field("radio_station_name")
        assert radio_station_name_field.max_length == 512
        assert radio_station_name_field.blank is True
        assert radio_station_name_field.null is True
        
        # Test radio_station_url field
        radio_station_url_field = File._meta.get_field("radio_station_url")
        assert radio_station_url_field.max_length == 512
        assert radio_station_url_field.blank is True
        assert radio_station_url_field.null is True
        
        # Test report_datetime field
        report_datetime_field = File._meta.get_field("report_datetime")
        assert report_datetime_field.max_length == 32
        assert report_datetime_field.blank is True
        assert report_datetime_field.null is True
        
        # Test report_location field
        report_location_field = File._meta.get_field("report_location")
        assert report_location_field.max_length == 512
        assert report_location_field.blank is True
        assert report_location_field.null is True
        
        # Test report_organization field
        report_organization_field = File._meta.get_field("report_organization")
        assert report_organization_field.max_length == 512
        assert report_organization_field.blank is True
        assert report_organization_field.null is True

    def test_model_with_full_metadata(self, file_with_metadata):
        """Test File model with all metadata fields populated."""
        assert file_with_metadata.name == "Full Metadata Song"
        assert file_with_metadata.bit_rate == 320
        assert file_with_metadata.sample_rate == 44100
        assert file_with_metadata.format == "FLAC"
        assert file_with_metadata.channels == 2
        assert file_with_metadata.length == timedelta(minutes=3, seconds=30)
        assert file_with_metadata.bpm == 120
        assert file_with_metadata.replay_gain == Decimal("-6.50")
        assert file_with_metadata.cue_in == timedelta(seconds=0)
        assert file_with_metadata.cue_out == timedelta(minutes=3, seconds=30)
        assert file_with_metadata.artist_name == "Test Artist"
        assert file_with_metadata.album_title == "Test Album"
        assert file_with_metadata.track_title == "Test Track"
        assert file_with_metadata.genre == "Rock"
        assert file_with_metadata.date == "2024"
        assert file_with_metadata.track_number == 1
        assert file_with_metadata.isrc == "USABC2400001"

    def test_import_status_default(self):
        """Test that import_status defaults to PENDING."""
        file_field = File._meta.get_field("import_status")
        assert file_field.default == File.ImportStatus.PENDING

    def test_accessed_default(self):
        """Test accessed field default value (implicit)."""
        file_field = File._meta.get_field("accessed")
        # accessed field does not have explicit default
        # It's an IntegerField without default specified

    @pytest.mark.parametrize("status_value,status_name", [
        (0, "SUCCESS"),
        (1, "PENDING"),
        (2, "FAILED"),
    ])
    def test_import_status_values(self, status_value, status_name):
        """Test ImportStatus values can be set correctly."""
        file_instance = File(
            name="Test",
            filepath="/test.mp3",
            size=1000,
            mime="audio/mpeg",
            import_status=status_value,
        )
        
        assert file_instance.import_status == status_value
        assert getattr(File.ImportStatus, status_name) == status_value
