from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from api.core.models.user import User


class Playlist(Model):

    class Meta:
        managed: bool = False
        app_label: str = "schedule"
        db_table: str = "cc_playlist"

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

    name: CharField = CharField(max_length=255)
    description: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )
    length: DurationField = DurationField(blank=True, null=True)

    owner: ForeignKey = ForeignKey(
        "core.User",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="creator_id",
    )

    def get_owner(self) -> "User | None":
        return self.owner


class PlaylistContent(Model):

    class Meta:
        managed: bool = False
        app_label: str = "schedule"
        db_table: str = "cc_playlistcontents"

    class Kind(IntegerChoices):
        FILE = 0, "File"
        STREAM = 1, "Stream"
        BLOCK = 2, "Block"

    playlist: ForeignKey = ForeignKey(
        "schedule.Playlist",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )

    kind: SmallIntegerField = SmallIntegerField(
        choices=Kind.choices,
        db_column="type",
    )

    file: ForeignKey = ForeignKey(
        "storage.File",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )
    stream: ForeignKey = ForeignKey(
        "schedule.Webstream",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )
    block: ForeignKey = ForeignKey(
        "schedule.SmartBlock",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )

    position: IntegerField = IntegerField(blank=True, null=True)
    offset: FloatField = FloatField(db_column="trackoffset")
    length: DurationField = DurationField(
        blank=True,
        null=True,
        db_column="cliplength",
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
    fade_in: TimeField = TimeField(
        blank=True,
        null=True,
        db_column="fadein",
    )
    fade_out: TimeField = TimeField(
        blank=True,
        null=True,
        db_column="fadeout",
    )

    def get_owner(self) -> "User | None":
        return self.playlist.get_owner()
