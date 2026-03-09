from typing import Any

from django.db.models import (
    DO_NOTHING,
    CharField,
    DateTimeField,
    DurationField,
    FloatField,
    ForeignKey,
    IntegerChoices,
    IntegerField,
    Model,
    SmallIntegerField,
    TimeField,
)


class Playlist(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_playlist"

    created_at: DateTimeField[Any, Any] = DateTimeField(
        blank=True, null=True, db_column="utime",
    )
    updated_at: DateTimeField[Any, Any] = DateTimeField(
        blank=True, null=True, db_column="mtime",
    )

    name: CharField[Any, Any] = CharField(max_length=255)
    description: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )
    length: DurationField[Any, Any] = DurationField(blank=True, null=True)

    owner: ForeignKey[Any, Any] = ForeignKey(
        "core.User",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="creator_id",
    )

    def get_owner(self):
        return self.owner


class PlaylistContent(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_playlistcontents"

    class Kind(IntegerChoices):
        FILE = 0, "File"
        STREAM = 1, "Stream"
        BLOCK = 2, "Block"

    playlist: ForeignKey[Any, Any] = ForeignKey(
        "schedule.Playlist",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )

    kind: SmallIntegerField[Any, Any] = SmallIntegerField(
        choices=Kind.choices,
        db_column="type",
    )

    file: ForeignKey[Any, Any] = ForeignKey(
        "storage.File",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )
    stream: ForeignKey[Any, Any] = ForeignKey(
        "schedule.Webstream",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )
    block: ForeignKey[Any, Any] = ForeignKey(
        "schedule.SmartBlock",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )

    position: IntegerField[Any, Any] = IntegerField(blank=True, null=True)
    offset: FloatField[Any, Any] = FloatField(db_column="trackoffset")
    length: DurationField[Any, Any] = DurationField(
        blank=True,
        null=True,
        db_column="cliplength",
    )
    cue_in: DurationField[Any, Any] = DurationField(
        blank=True, null=True, db_column="cuein",
    )
    cue_out: DurationField[Any, Any] = DurationField(
        blank=True, null=True, db_column="cueout",
    )
    fade_in: TimeField[Any, Any] = TimeField(
        blank=True, null=True, db_column="fadein",
    )
    fade_out: TimeField[Any, Any] = TimeField(
        blank=True, null=True, db_column="fadeout",
    )

    def get_owner(self):
        return self.playlist.get_owner()
