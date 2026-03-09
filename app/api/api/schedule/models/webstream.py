from typing import final

from django.db import models


@final
class Webstream(models.Model):

    @final
    class Meta:
        managed: bool = False
        db_table: str = "cc_webstream"
        permissions: tuple[tuple[str, str], ...] = (
            (
                "change_own_webstream",
                "Change the webstreams where they are the owner",
            ),
            (
                "delete_own_webstream",
                "Delete the webstreams where they are the owner",
            ),
        )

    created_at = models.DateTimeField(db_column="utime")
    updated_at = models.DateTimeField(db_column="mtime")

    last_played_at = models.DateTimeField(
        blank=True,
        null=True,
        db_column="lptime",
    )

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    url = models.CharField(max_length=512)
    length = models.DurationField()
    mime = models.CharField(max_length=1024, blank=True, null=True)

    owner = models.ForeignKey(
        "core.User",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="creator_id",
    )

    def get_owner(self):
        return self.owner


@final
class WebstreamMetadata(models.Model):

    @final
    class Meta:
        managed: bool = False
        db_table: str = "cc_webstream_metadata"

    schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.DO_NOTHING,
        db_column="instance_id",
    )
    starts_at = models.DateTimeField(db_column="start_time")
    data = models.CharField(max_length=1024, db_column="liquidsoap_data")

    def get_owner(self):
        return self.schedule.get_owner()
