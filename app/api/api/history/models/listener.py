from django.db import models

from api.fields import TimezoneAwareDateTimeField


class MountName(models.Model):
    mount_name = models.CharField(max_length=1024)

    class Meta:
        managed = False
        app_label = "history"
        db_table = "cc_mount_name"


class Timestamp(models.Model):
    timestamp = TimezoneAwareDateTimeField()

    class Meta:
        managed = False
        app_label = "history"
        db_table = "cc_timestamp"


class ListenerCount(models.Model):
    timestamp = models.ForeignKey(
        "history.Timestamp",
        on_delete=models.DO_NOTHING,
    )
    mount_name = models.ForeignKey(
        "history.MountName",
        on_delete=models.DO_NOTHING,
    )
    listener_count = models.IntegerField()

    class Meta:
        managed = False
        app_label = "history"
        db_table = "cc_listener_count"
