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

    library: ForeignKey = ForeignKey(
        "storage.Library",
        DO_NOTHING,
        blank=True,
        null=True,
        db_column="track_type_id",
    )

    owner: ForeignKey = ForeignKey(
        "core.User",
        DO_NOTHING,
        blank=True,
        null=True,
    )

    import_status: IntegerField = IntegerField(
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
    )

    filepath: TextField = TextField(blank=True, null=True)
    size: IntegerField = IntegerField(db_column="filesize")
    exists: BooleanField = BooleanField(
        blank=True,
        null=True,
        db_column="file_exists",
    )
    mime: CharField = CharField(max_length=255)
    md5: CharField = CharField(max_length=32, blank=True, null=True)

    hidden: BooleanField = BooleanField(blank=True, null=True)
    accessed: IntegerField = IntegerField(
        db_column="currentlyaccessing",
    )
    scheduled: BooleanField = BooleanField(
        blank=True,
        null=True,
        db_column="is_scheduled",
    )
    part_of_list: BooleanField = BooleanField(
        blank=True,
        null=True,
        db_column="is_playlist",
    )

    created_at: DateTimeField = DateTimeField(
        blank=True,
        null=True,
        db_column="utime",
    )
    updated_at: DateTimeField = DateTimeField(
        blank=True,
        null=True,
        db_column="mtime",
    )
    last_played_at: DateTimeField = DateTimeField(
        blank=True,
        null=True,
        db_column="lptime",
    )

    edited_by: ForeignKey = ForeignKey(
        "core.User",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        related_name="edited_files",
        db_column="editedby",
    )

    # Audio
    bit_rate: IntegerField = IntegerField(blank=True, null=True)
    sample_rate: IntegerField = IntegerField(blank=True, null=True)
    format: CharField = CharField(
        max_length=128,
        blank=True,
        null=True,
    )  # ?
    channels: IntegerField = IntegerField(blank=True, null=True)
    length: DurationField = DurationField(blank=True, null=True)

    bpm: IntegerField = IntegerField(blank=True, null=True)  # ?
    replay_gain: DecimalField = DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    cue_in: DurationField = DurationField(
        blank=True,
        null=True,
        db_column="cuein",
    )
    cue_out: DurationField = DurationField(
        blank=True,
        null=True,
        db_column="cueout",
    )

    # Metadata
    name: CharField = CharField(max_length=255)  # ?
    description: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    artwork: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )

    artist_name: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    artist_url: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    original_artist: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    album_title: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    track_title: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    genre: CharField = CharField(
        max_length=64,
        blank=True,
        null=True,
    )
    mood: CharField = CharField(max_length=64, blank=True, null=True)
    date: CharField = CharField(
        max_length=16,
        blank=True,
        null=True,
        db_column="year",
    )
    track_number: IntegerField = IntegerField(blank=True, null=True)
    disc_number: CharField = CharField(
        max_length=8,
        blank=True,
        null=True,
    )  # ?
    comment: TextField = TextField(
        blank=True,
        null=True,
        db_column="comments",
    )
    language: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    label: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    copyright: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    composer: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    conductor: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    orchestra: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    encoder: CharField = CharField(
        max_length=64,
        blank=True,
        null=True,
    )
    encoded_by: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
    )  # ?
    isrc: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
        db_column="isrc_number",
    )

    lyrics: TextField = TextField(blank=True, null=True)  # ?
    lyricist: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    original_lyricist: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    subject: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    contributor: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    rating: CharField = CharField(
        max_length=8,
        blank=True,
        null=True,
    )  # ?
    url: CharField = CharField(
        max_length=1024,
        blank=True,
        null=True,
    )  # ?
    info_url: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    audio_source_url: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    buy_this_url: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    catalog_number: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    radio_station_name: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    radio_station_url: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    report_datetime: CharField = CharField(
        max_length=32,
        blank=True,
        null=True,
    )  # ?
    report_location: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?
    report_organization: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )  # ?

    def get_owner(self):
        return self.owner
