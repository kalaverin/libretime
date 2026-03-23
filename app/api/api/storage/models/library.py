from typing import final

from django.db.models import (
    AutoField,
    BooleanField,
    CharField,
    Model,
)


@final
class Library(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_track_types"

    name: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column="type_name",
    )

    code: CharField = CharField(max_length=16, unique=True)

    description: CharField = CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    enabled: BooleanField = BooleanField(
        blank=True,
        default=True,
        db_column="visibility",
    )

    analyze_cue_points: BooleanField = BooleanField(
        blank=True,
        default=True,
        db_column="analyze_cue_points",
    )

    id: AutoField = AutoField(primary_key=True)
