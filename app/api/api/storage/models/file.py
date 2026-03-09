from typing import Any, final

from django.db import models
from django.db.models import (
    DO_NOTHING,
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    DurationField,
    ForeignKey,
    IntegerField,
    Model,
    TextField,
)


@final
class File(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_files"
        permissions: tuple[tuple[str, str], ...] = (
            ("change_own_file", "Change the files where they are the owner"),
            ("delete_own_file", "Delete the files where they are the owner"),
        )

    class ImportStatus(models.IntegerChoices):
        SUCCESS = 0, "Success"
        PENDING = 1, "Pending"
        FAILED = 2, "Failed"

    library: ForeignKey[Any, Any] = ForeignKey(
        "storage.Library",
        DO_NOTHING,
        blank=True,
        null=True,
        db_column="track_type_id",
    )

    owner: ForeignKey[Any, Any] = ForeignKey(
        "core.User",
        DO_NOTHING,
        blank=True,
        null=True,
    )

    import_status: IntegerField[Any, Any] = IntegerField(
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
    )

    filepath: TextField[Any, Any] = TextField(blank=True, null=True)
    size: IntegerField[Any, Any] = IntegerField(db_column="filesize")
    exists: BooleanField[Any, Any] = BooleanField(
        blank=True,
        null=True,
        db_column="file_exists",
    )
    mime: CharField[Any, Any] = CharField(max_length=255)
    md5: CharField[Any, Any] = CharField(max_length=32, blank=True, null=True)

    hidden: BooleanField[Any, Any] = BooleanField(blank=True, null=True)
    accessed: IntegerField[Any, Any] = IntegerField(
        db_column="currentlyaccessing",
    )
    scheduled: BooleanField[Any, Any] = BooleanField(
        blank=True,
        null=True,
        db_column="is_scheduled",
    )
    part_of_list: BooleanField[Any, Any] = BooleanField(
        blank=True,
        null=True,
        db_column="is_playlist",
    )

    created_at: DateTimeField[Any, Any] = DateTimeField(
        blank=True, null=True, db_column="utime",
    )
    updated_at: DateTimeField[Any, Any] = DateTimeField(
        blank=True, null=True, db_column="mtime",
    )
    last_played_at: DateTimeField[Any, Any] = DateTimeField(
        blank=True,
        null=True,
        db_column="lptime",
    )

    edited_by: ForeignKey[Any, Any] = ForeignKey(
        "core.User",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        related_name="edited_files",
        db_column="editedby",
    )

    # Audio
    bit_rate: IntegerField[Any, Any] = IntegerField(blank=True, null=True)
    sample_rate: IntegerField[Any, Any] = IntegerField(blank=True, null=True)
    format: CharField[Any, Any] = CharField(
        max_length=128, blank=True, null=True,
    )  # ?
    channels: IntegerField[Any, Any] = IntegerField(blank=True, null=True)
    length: DurationField[Any, Any] = DurationField(blank=True, null=True)

    bpm: IntegerField[Any, Any] = IntegerField(blank=True, null=True)  # ?
    replay_gain: DecimalField[Any, Any] = DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    cue_in: DurationField[Any, Any] = DurationField(
        blank=True, null=True, db_column="cuein",
    )
    cue_out: DurationField[Any, Any] = DurationField(
        blank=True, null=True, db_column="cueout",
    )

    # Metadata
    name: CharField[Any, Any] = CharField(max_length=255)  # ?
    description: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?

    artwork: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )

    artist_name: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    artist_url: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    original_artist: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    album_title: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    track_title: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    genre: CharField[Any, Any] = CharField(
        max_length=64, blank=True, null=True,
    )
    mood: CharField[Any, Any] = CharField(max_length=64, blank=True, null=True)
    date: CharField[Any, Any] = CharField(
        max_length=16,
        blank=True,
        null=True,
        db_column="year",
    )
    track_number: IntegerField[Any, Any] = IntegerField(blank=True, null=True)
    disc_number: CharField[Any, Any] = CharField(
        max_length=8, blank=True, null=True,
    )  # ?
    comment: TextField[Any, Any] = TextField(
        blank=True, null=True, db_column="comments",
    )
    language: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    label: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    copyright: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    composer: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    conductor: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    orchestra: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    encoder: CharField[Any, Any] = CharField(
        max_length=64, blank=True, null=True,
    )
    encoded_by: CharField[Any, Any] = CharField(
        max_length=255, blank=True, null=True,
    )  # ?
    isrc: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
        db_column="isrc_number",
    )

    lyrics: TextField[Any, Any] = TextField(blank=True, null=True)  # ?
    lyricist: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    original_lyricist: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    subject: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    contributor: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    rating: CharField[Any, Any] = CharField(
        max_length=8, blank=True, null=True,
    )  # ?
    url: CharField[Any, Any] = CharField(
        max_length=1024, blank=True, null=True,
    )  # ?
    info_url: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    audio_source_url: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    buy_this_url: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )  # ?
    catalog_number: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    radio_station_name: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    radio_station_url: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    report_datetime: CharField[Any, Any] = CharField(
        max_length=32,
        blank=True,
        null=True,
    )  # ?
    report_location: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    report_organization: CharField[Any, Any] = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    def get_owner(self):
        return self.owner
