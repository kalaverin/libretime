
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

    kind: CharField = CharField(
        choices=Kind.choices,
        default=Kind.DYNAMIC,
        max_length=7,
        blank=True,
        null=True,
        db_column="type",
    )

    owner: ForeignKey = ForeignKey(
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

    block: ForeignKey = ForeignKey(
        "schedule.SmartBlock",
        on_delete=DO_NOTHING,
        blank=True,
        null=True,
    )
    file: ForeignKey = ForeignKey(
        "storage.File",
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

    block: ForeignKey = ForeignKey(
        "schedule.SmartBlock",
        on_delete=DO_NOTHING,
    )
    group: IntegerField = IntegerField(
        blank=True,
        null=True,
        db_column="criteriagroup",
    )

    criteria: CharField = CharField(max_length=32)
    condition: CharField = CharField(
        max_length=16,
        db_column="modifier",
    )
    value: CharField = CharField(max_length=512)
    extra: CharField = CharField(
        max_length=512,
        blank=True,
        null=True,
    )

    def get_owner(self):
        return self.block.get_owner()
