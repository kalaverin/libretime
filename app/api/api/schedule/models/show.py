from typing import TYPE_CHECKING

from django.db.models import (
    DO_NOTHING,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DurationField,
    ForeignKey,
    IntegerChoices,
    ManyToManyField,
    Model,
    SmallIntegerField,
    TimeField,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from api.core.models.user import User


class Show(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_show"

    name: CharField = CharField(max_length=255)
    description: CharField = CharField(
        max_length=8192,
        blank=True,
        null=True,
    )
    genre: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    url: CharField = CharField(max_length=255, blank=True, null=True)

    image: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column="image_path",
    )
    foreground_color: CharField = CharField(
        max_length=6,
        blank=True,
        null=True,
        db_column="color",
    )
    background_color: CharField = CharField(
        max_length=6,
        blank=True,
        null=True,
    )

    live_auth_registered: BooleanField = BooleanField(
        default=False,
        blank=True,
        null=True,
        db_column="live_stream_using_airtime_auth",
    )
    live_auth_custom: BooleanField = BooleanField(
        default=False,
        blank=True,
        null=True,
        db_column="live_stream_using_custom_auth",
    )
    live_auth_custom_user: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column="live_stream_user",
    )
    live_auth_custom_password: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column="live_stream_pass",
    )

    @property
    def live_enabled(self) -> bool:
        return any((self.live_auth_registered, self.live_auth_custom))

    # A show is linkable if it has never been linked before. Once
    # a show becomes unlinked it can not be linked again.
    linked: BooleanField = BooleanField()
    linkable: BooleanField = BooleanField(db_column="is_linkable")

    auto_playlist: ForeignKey = ForeignKey(
        "schedule.Playlist",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="autoplaylist_id",
    )
    auto_playlist_enabled: BooleanField = BooleanField(
        db_column="has_autoplaylist",
    )
    auto_playlist_repeat: BooleanField = BooleanField(
        db_column="autoplaylist_repeat",
    )

    intro_playlist: ForeignKey = ForeignKey(
        "schedule.Playlist",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="intro_playlist_id",
        related_name="intro_playlist",
    )

    override_intro_playlist: BooleanField = BooleanField(
        db_column="override_intro_playlist",
    )

    outro_playlist: ForeignKey = ForeignKey(
        "schedule.Playlist",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="outro_playlist_id",
        related_name="outro_playlist",
    )

    override_outro_playlist: BooleanField = BooleanField(
        db_column="override_outro_playlist",
    )

    hosts: ManyToManyField = ManyToManyField(
        "core.User",
        through="ShowHost",
    )

    def get_owner(self) -> "QuerySet[User]":
        return self.hosts.all()


class ShowHost(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_show_hosts"

    show: ForeignKey = ForeignKey(
        "schedule.Show",
        on_delete=DO_NOTHING,
    )
    user: ForeignKey = ForeignKey(
        "core.User",
        on_delete=DO_NOTHING,
        db_column="subjs_id",
    )


# TODO: Replace record choices with a boolean
class Record(IntegerChoices):
    NO = 0, "No"
    YES = 1, "Yes"


class ShowDays(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_show_days"

    class WeekDay(IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    class RepeatKind(IntegerChoices):
        WEEKLY = 0, "Every week"
        WEEKLY_2 = 1, "Every 2 weeks"
        WEEKLY_3 = 4, "Every 3 weeks"
        WEEKLY_4 = 5, "Every 4 weeks"
        MONTHLY = 2, "Every month"

    show: ForeignKey = ForeignKey(
        "schedule.Show",
        on_delete=DO_NOTHING,
    )

    first_show_on: DateField = DateField(
        db_column="first_show",
    )
    last_show_on: DateField = DateField(
        blank=True,
        null=True,
        db_column="last_show",
    )
    start_time: TimeField = TimeField()

    timezone: CharField = CharField(max_length=1024)
    duration: CharField = CharField(max_length=1024)

    record_enabled: SmallIntegerField = SmallIntegerField(
        choices=Record.choices,
        default=Record.NO,
        blank=True,
        null=True,
        db_column="record",
    )

    week_day: SmallIntegerField = SmallIntegerField(
        choices=WeekDay.choices,
        blank=True,
        null=True,
        db_column="day",
    )

    repeat_kind: SmallIntegerField = SmallIntegerField(
        choices=RepeatKind.choices,
        db_column="repeat_type",
    )
    repeat_next_on: DateField = DateField(
        blank=True,
        null=True,
        db_column="next_pop_date",
    )

    def get_owner(self) -> "QuerySet[User]":
        return self.show.get_owner()


class ShowInstance(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_show_instances"

    created_at: DateTimeField = DateTimeField(db_column="created")

    show: ForeignKey = ForeignKey(
        "schedule.Show",
        on_delete=DO_NOTHING,
    )
    instance: ForeignKey = ForeignKey(
        "self",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )

    starts_at: DateTimeField = DateTimeField(db_column="starts")
    ends_at: DateTimeField = DateTimeField(db_column="ends")
    filled_time: DurationField = DurationField(
        blank=True,
        null=True,
        db_column="time_filled",
    )

    last_scheduled_at: DateTimeField = DateTimeField(
        blank=True,
        null=True,
        db_column="last_scheduled",
    )

    description: CharField = CharField(
        max_length=8192,
        blank=True,
        null=True,
    )
    modified: BooleanField = BooleanField(
        db_column="modified_instance",
    )
    rebroadcast: SmallIntegerField = SmallIntegerField(
        blank=True,
        null=True,
    )

    auto_playlist_built: BooleanField = BooleanField(
        db_column="autoplaylist_built",
    )

    record_enabled: SmallIntegerField = SmallIntegerField(
        choices=Record.choices,
        default=Record.NO,
        blank=True,
        null=True,
        db_column="record",
    )
    record_file: ForeignKey = ForeignKey(
        "storage.File",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="file_id",
    )

    def get_owner(self) -> "QuerySet[User]":
        return self.show.get_owner()


class ShowRebroadcast(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_show_rebroadcast"

    show: ForeignKey = ForeignKey(
        "schedule.Show",
        on_delete=DO_NOTHING,
    )
    day_offset: CharField = CharField(max_length=1024)
    start_time: TimeField = TimeField()

    def get_owner(self) -> "QuerySet[User]":
        return self.show.get_owner()
