from django.db import models

from api.fields import TimezoneAwareDateTimeField


class LiveLog(models.Model):
    state = models.CharField(max_length=32)
    start_time = TimezoneAwareDateTimeField()
    end_time = TimezoneAwareDateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        app_label = "history"
        db_table = "cc_live_log"
