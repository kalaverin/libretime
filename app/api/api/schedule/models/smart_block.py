from typing import Any

from django.db.models import (
    DO_NOTHING,
    CharField,
    DateTimeField,
    DurationField,
    FloatField,
    ForeignKey,
    IntegerField,
    Model,
    TextChoices,
    TimeField,
)


class SmartBlock(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_block"
        permissions: tuple[tuple[str, str], ...] = (
            (
                "change_own_smartblock",
                "Change the smartblocks where they are the owner",
            ),
            (
                "delete_own_smartblock",
                "Delete the smartblocks where they are the owner",
            ),
        )

    class Kind(TextChoices):
        STATIC = "static", "Static"
        DYNAMIC = "dynamic", "Dynamic"

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

    kind: CharField[Any, Any] = CharField(
        choices=Kind.choices,
        default=Kind.DYNAMIC,
        max_length=7,
        blank=True,
        null=True,
        db_column="type",
    )

    owner: ForeignKey[Any, Any] = ForeignKey(
        "core.User",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
        db_column="creator_id",
    )

    def get_owner(self):
        return self.owner


class SmartBlockContent(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_blockcontents"
        permissions: tuple[tuple[str, str], ...] = (
            (
                "change_own_smartblockcontent",
                "Change the content of smartblocks where they are the owner",
            ),
            (
                "delete_own_smartblockcontent",
                "Delete the content of smartblocks where they are the owner",
            ),
        )

    block: ForeignKey[Any, Any] = ForeignKey(
        "schedule.SmartBlock",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )
    file: ForeignKey[Any, Any] = ForeignKey(
        "storage.File",
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
        return self.block.get_owner()


class SmartBlockCriteria(Model):

    class Meta:
        managed: bool = False
        db_table: str = "cc_blockcriteria"
        permissions: tuple[tuple[str, str], ...] = (
            (
                "change_own_smartblockcriteria",
                "Change the criteria of smartblocks where they are the owner",
            ),
            (
                "delete_own_smartblockcriteria",
                "Delete the criteria of smartblocks where they are the owner",
            ),
        )

    block: ForeignKey[Any, Any] = ForeignKey(
        "schedule.SmartBlock",
        on_delete=DO_NOTHING,
    )
    group: IntegerField[Any, Any] = IntegerField(
        blank=True,
        null=True,
        db_column="criteriagroup",
    )

    criteria: CharField[Any, Any] = CharField(max_length=32)
    condition: CharField[Any, Any] = CharField(
        max_length=16, db_column="modifier",
    )
    value: CharField[Any, Any] = CharField(max_length=512)
    extra: CharField[Any, Any] = CharField(
        max_length=512, blank=True, null=True,
    )

    def get_owner(self):
        return self.block.get_owner()
