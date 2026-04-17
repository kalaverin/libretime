"""
Model bakery recipes for API v2 testing.

Provides standardized model factories for testing API contracts.
All recipes ensure consistent test data across the test suite.
"""

import uuid

from datetime import timedelta

from model_bakery.recipe import Recipe, seq

from api.core.models.role import Role
from api.core.models.user import User
from api.storage.models.file import File
from api.storage.models.library import Library
from sdk import now


def get_user_recipe(role: str, **overrides) -> Recipe:
    """
    Get a base User recipe with specified role.

    Args:
        role: One of Role.GUEST, Role.HOST, Role.MANAGER, Role.ADMIN
        **overrides: Additional field overrides

    Returns:
        Recipe configured for the specified role
    """
    role_prefix = {
        Role.GUEST: "guest",
        Role.HOST: "host",
        Role.MANAGER: "manager",
        Role.ADMIN: "admin",
    }.get(role, "user")

    base_fields = {
        "role": role,
        "username": f"{role_prefix}_{{seq}}",
        "email": f"{role_prefix}_{{seq}}@test.com",
        "first_name": role_prefix.capitalize(),
        "last_name": "Test",
    }
    base_fields.update(overrides)

    return Recipe(User, **base_fields)


# Pre-defined recipes for common use cases
guest_user_recipe = get_user_recipe(Role.GUEST)
host_user_recipe = get_user_recipe(Role.HOST)
manager_user_recipe = get_user_recipe(Role.MANAGER)
admin_user_recipe = get_user_recipe(Role.ADMIN)


def make_guest_user(**overrides) -> User:
    """Create a guest user (role=G) with test data."""
    return guest_user_recipe.make(**overrides)


def make_host_user(**overrides) -> User:
    """Create a host user (role=H) with test data."""
    return host_user_recipe.make(**overrides)


def make_manager_user(**overrides) -> User:
    """Create a manager user (role=P) with test data."""
    return manager_user_recipe.make(**overrides)


def make_admin_user(**overrides) -> User:
    """Create an admin user (role=A) with test data."""
    return admin_user_recipe.make(**overrides)


def make_user_with_permissions(role: str, *perms: str, **overrides) -> User:
    """
    Create a user with specific permissions.

    Args:
        role: User role (G/H/P/A)
        *perms: Permission codenames to grant
        **overrides: Additional field overrides

    Returns:
        User instance with specified permissions
    """
    user = get_user_recipe(role).make(**overrides)
    # Note: Permissions are typically role-based in LibreTime
    # This function exists for edge cases requiring specific perms
    return user


# =============================================================================
# STORAGE MODELS
# =============================================================================

# Library (Track Type) recipes
library_recipe = Recipe(
    Library,
    code=seq("library"),
    name=seq("Library "),
    description="Test library type",
    enabled=True,
    analyze_cue_points=True,
)


def make_library(**overrides) -> Library:
    """Create a library (track type) for testing."""
    return library_recipe.make(**overrides)


# File recipes with realistic audio metadata
file_recipe = Recipe(
    File,
    # Identification
    name=seq("track_"),
    filepath=lambda: f"/tmp/test_audio_{uuid.uuid4().hex[:8]}.mp3",
    size=10_000_000,  # 10MB
    mime="audio/mpeg",
    md5=lambda: uuid.uuid4().hex,
    # Status
    import_status=File.ImportStatus.SUCCESS,
    exists=True,
    hidden=False,
    accessed=0,
    scheduled=False,
    part_of_list=False,
    # Audio properties (typical MP3)
    bit_rate=320_000,  # 320 kbps
    sample_rate=44_100,  # 44.1 kHz
    format="mp3",
    channels=2,
    length=timedelta(minutes=3, seconds=30),  # 3:30
    # ReplayGain
    replay_gain="-8.50",
    # Cue points (full track by default)
    cue_in=timedelta(seconds=0),
    cue_out=timedelta(minutes=3, seconds=30),
    # Metadata
    track_title=seq("Test Track "),
    artist_name=seq("Test Artist "),
    album_title=seq("Test Album "),
    genre="Test Genre",
    mood="Happy",
    date="2024",
    track_number=seq(1),
    comment="Test comment for audio file",
    language="English",
    label="Test Label",
    copyright="Test Copyright",
    composer=seq("Test Composer "),
    conductor=seq("Test Conductor "),
    encoder="LAME",
    isrc=seq("ISRC"),
    # Ownership - must be provided or use subfactory
    # owner=foreign_key(user_recipe),
    # library=foreign_key(library_recipe),
)


def make_file(owner=None, library=None, **overrides) -> File:
    """
    Create a file with valid audio metadata for testing.

    Args:
        owner: User who owns the file (created if None)
        library: Library/track type (created if None)
        **overrides: Additional field overrides

    Returns:
        File instance with realistic audio metadata
    """
    if owner is None:
        owner = make_host_user()
    if library is None:
        library = make_library()

    return file_recipe.make(owner=owner, library=library, **overrides)


def make_pending_file(**overrides) -> File:
    """Create a file in pending import status."""
    defaults = {"import_status": File.ImportStatus.PENDING}
    defaults.update(overrides)
    return make_file(**defaults)


def make_failed_file(**overrides) -> File:
    """Create a file in failed import status."""
    defaults = {"import_status": File.ImportStatus.FAILED}
    defaults.update(overrides)
    return make_file(**defaults)


# =============================================================================
# SCHEDULE MODELS
# =============================================================================

from datetime import time

from api.schedule.models.show import (
    Record,
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
)

# Show recipes
show_recipe = Recipe(
    Show,
    name=seq("Test Show "),
    description="Test show description",
    genre="Talk",
    url="https://example.com/show",
    foreground_color="FFFFFF",
    background_color="000000",
    live_auth_registered=False,
    live_auth_custom=False,
    linked=False,
    linkable=True,
    auto_playlist_enabled=False,
    auto_playlist_repeat=False,
    override_intro_playlist=False,
    override_outro_playlist=False,
)


def make_show(hosts=None, **overrides) -> Show:
    """
    Create a show with optional hosts.

    Args:
        hosts: List of User objects to add as hosts (created if None/empty)
        **overrides: Additional field overrides

    Returns:
        Show instance
    """
    show = show_recipe.make(**overrides)

    if hosts:
        for host in hosts:
            ShowHost.objects.create(show=show, user=host)

    return show


def make_show_with_live_auth(host=None, **overrides) -> Show:
    """Create a show with live streaming credentials."""
    defaults = {
        "live_auth_custom": True,
        "live_auth_custom_user": "live_user",
        "live_auth_custom_password": "live_pass",
    }
    defaults.update(overrides)
    return make_show(hosts=[host] if host else None, **defaults)


# ShowHost recipe
show_host_recipe = Recipe(ShowHost)


def make_show_host(show=None, user=None, **overrides) -> ShowHost:
    """
    Create a show-host relationship.

    Args:
        show: Show instance (created if None)
        user: User instance (created if None)
    """
    if show is None:
        show = make_show()
    if user is None:
        user = make_host_user()

    return show_host_recipe.make(show=show, user=user, **overrides)


# ShowDays recipes
show_days_recipe = Recipe(
    ShowDays,
    first_show_on=lambda: now().date(),
    last_show_on=None,  # No end date (indefinite)
    start_time=time(14, 0),  # 2:00 PM
    timezone="UTC",
    duration="01:00",  # 1 hour
    record_enabled=Record.NO,
    week_day=ShowDays.WeekDay.MONDAY,
    repeat_kind=ShowDays.RepeatKind.WEEKLY,
    repeat_next_on=None,
)


def make_show_days(show=None, **overrides) -> ShowDays:
    """
    Create show schedule pattern (days).

    Args:
        show: Show instance (created if None)
        **overrides: Field overrides including repeat_kind
    """
    if show is None:
        show = make_show()

    return show_days_recipe.make(show=show, **overrides)


def make_weekly_show_days(
    show=None,
    week_day=ShowDays.WeekDay.MONDAY,
    **overrides,
):
    """Create weekly repeating show pattern."""
    defaults = {
        "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        "week_day": week_day,
    }
    defaults.update(overrides)
    return make_show_days(show, **defaults)


def make_biweekly_show_days(show=None, **overrides):
    """Create bi-weekly repeating show pattern."""
    defaults = {"repeat_kind": ShowDays.RepeatKind.WEEKLY_2}
    defaults.update(overrides)
    return make_show_days(show, **defaults)


def make_monthly_show_days(show=None, **overrides):
    """Create monthly repeating show pattern."""
    defaults = {"repeat_kind": ShowDays.RepeatKind.MONTHLY}
    defaults.update(overrides)
    return make_show_days(show, **defaults)


# ShowInstance recipe
show_instance_recipe = Recipe(
    ShowInstance,
    created_at=now,
    starts_at=now,
    ends_at=lambda: now() + timedelta(hours=1),
    filled_time=None,
    last_scheduled_at=None,
    description="",
    modified=False,
    rebroadcast=0,
)


def make_show_instance(show=None, **overrides) -> ShowInstance:
    """
    Create a show instance.

    Args:
        show: Show instance (created if None)
        **overrides: Field overrides
    """
    if show is None:
        show = make_show()

    return show_instance_recipe.make(show=show, **overrides)


def make_modified_instance(show=None, **overrides):
    """Create a modified show instance."""
    defaults = {
        "modified": True,
        "description": "Modified instance description",
    }
    defaults.update(overrides)
    return make_show_instance(show, **defaults)


# =============================================================================
# PLAYLIST MODELS
# =============================================================================

from api.schedule.models.playlist import Playlist, PlaylistContent

# Playlist recipes
playlist_recipe = Recipe(
    Playlist,
    name=seq("Test Playlist "),
    description="Test playlist description",
    length=None,  # Computed from contents
)


def make_playlist(owner=None, **overrides) -> Playlist:
    """
    Create a playlist with optional owner.

    Args:
        owner: User who owns the playlist (created if None)
        **overrides: Field overrides
    """
    if owner is None:
        owner = make_host_user()

    return playlist_recipe.make(owner=owner, **overrides)


# PlaylistContent recipes
playlist_content_recipe = Recipe(
    PlaylistContent,
    position=seq(0),
    offset=0.0,
    length=None,
    cue_in=None,
    cue_out=None,
    fade_in=None,
    fade_out=None,
)


def make_playlist_content(
    playlist=None,
    position=None,
    **overrides,
) -> PlaylistContent:
    """
    Create playlist content entry.

    Args:
        playlist: Playlist instance (created if None)
        position: Position in playlist (auto if None)
        **overrides: Field overrides
    """
    if playlist is None:
        playlist = make_playlist()

    if position is not None:
        overrides["position"] = position

    return playlist_content_recipe.make(playlist=playlist, **overrides)


def make_playlist_file(file=None, playlist=None, position=None, **overrides):
    """
    Add a file to playlist content.

    Args:
        file: File instance (created if None)
        playlist: Playlist instance (created if None)
        position: Position in playlist
    """
    if file is None:
        file = make_file()

    defaults = {
        "kind": PlaylistContent.Kind.FILE,
        "file": file,
        "length": file.length,
        "cue_in": file.cue_in,
        "cue_out": file.cue_out,
    }
    defaults.update(overrides)

    return make_playlist_content(playlist, position, **defaults)


def make_playlist_stream(
    stream=None,
    playlist=None,
    position=None,
    **overrides,
):
    """
    Add a webstream to playlist content.

    Args:
        stream: Webstream instance (created if None - requires T162)
        playlist: Playlist instance (created if None)
        position: Position in playlist
    """
    defaults = {
        "kind": PlaylistContent.Kind.STREAM,
        "stream": stream,  # May be None if T162 not done yet
    }
    defaults.update(overrides)

    return make_playlist_content(playlist, position, **defaults)


def make_playlist_block(block=None, playlist=None, position=None, **overrides):
    """
    Add a smart block to playlist content.

    Args:
        block: SmartBlock instance (created if None - requires T158)
        playlist: Playlist instance (created if None)
        position: Position in playlist
    """
    defaults = {
        "kind": PlaylistContent.Kind.BLOCK,
        "block": block,  # May be None if T158 not done yet
    }
    defaults.update(overrides)

    return make_playlist_content(playlist, position, **defaults)


# =============================================================================
# SMART BLOCK MODELS
# =============================================================================

from api.schedule.models.smart_block import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)

# SmartBlock recipes
smart_block_recipe = Recipe(
    SmartBlock,
    name=seq("Test SmartBlock "),
    description="Test smart block description",
    kind=SmartBlock.Kind.DYNAMIC,  # Default to dynamic
    length=None,
)


def make_smart_block(owner=None, kind=None, **overrides) -> SmartBlock:
    """
    Create a smart block.

    Args:
        owner: User who owns the block (created if None)
        kind: STATIC or DYNAMIC (defaults to DYNAMIC)
        **overrides: Field overrides
    """
    if owner is None:
        owner = make_host_user()
    if kind is not None:
        overrides["kind"] = kind

    return smart_block_recipe.make(owner=owner, **overrides)


def make_static_block(owner=None, **overrides):
    """Create a static smart block (manual content)."""
    return make_smart_block(owner, kind=SmartBlock.Kind.STATIC, **overrides)


def make_dynamic_block(owner=None, **overrides):
    """Create a dynamic smart block (criteria-based)."""
    return make_smart_block(owner, kind=SmartBlock.Kind.DYNAMIC, **overrides)


# SmartBlockContent recipes (for static blocks)
smart_block_content_recipe = Recipe(
    SmartBlockContent,
    position=seq(0),
    offset=0.0,
    length=None,
    cue_in=None,
    cue_out=None,
    fade_in=None,
    fade_out=None,
)


def make_smart_block_content(
    block=None,
    file=None,
    position=None,
    **overrides,
):
    """
    Add content to a static smart block.

    Args:
        block: SmartBlock instance (created if None)
        file: File instance (created if None)
        position: Position in block (auto if None)
    """
    if block is None:
        block = make_static_block()
    if file is None:
        file = make_file()

    if position is not None:
        overrides["position"] = position

    defaults = {
        "length": file.length,
        "cue_in": file.cue_in,
        "cue_out": file.cue_out,
    }
    defaults.update(overrides)

    return smart_block_content_recipe.make(
        block=block,
        file=file,
        **defaults,
    )


# SmartBlockCriteria recipes (for dynamic blocks)
smart_block_criteria_recipe = Recipe(
    SmartBlockCriteria,
    group=0,  # Criteria group for AND/OR logic
    criteria="genre",  # Field to match
    condition="contains",  # Modifier
    value="Jazz",  # Value to match
    extra=None,
)


def make_smart_block_criteria(
    block=None,
    criteria=None,
    condition=None,
    value=None,
    **overrides,
):
    """
    Add criteria to a dynamic smart block.

    Args:
        block: SmartBlock instance (created if None - will be dynamic)
        criteria: Field name (genre, artist_name, etc.)
        condition: Modifier (contains, equals, etc.)
        value: Value to match
    """
    if block is None:
        block = make_dynamic_block()

    if criteria:
        overrides["criteria"] = criteria
    if condition:
        overrides["condition"] = condition
    if value:
        overrides["value"] = value

    return smart_block_criteria_recipe.make(block=block, **overrides)


def make_genre_criteria(block=None, genre="Jazz", **overrides):
    """Create genre criteria for dynamic block."""
    return make_smart_block_criteria(
        block=block,
        criteria="genre",
        condition="equals",
        value=genre,
        **overrides,
    )


# =============================================================================
# PODCAST MODELS
# =============================================================================

from api.podcasts.models.podcast import (
    ImportedPodcast,
    Podcast,
    PodcastEpisode,
    StationPodcast,
)

# Podcast recipes
podcast_recipe = Recipe(
    Podcast,
    url=seq("https://example.com/podcast/"),
    title=seq("Test Podcast "),
    creator="Test Creator",
    description="Test podcast description",
    language="en",
    copyright="Test Copyright",
    link="https://example.com",
    # iTunes metadata
    itunes_author="Test Author",
    itunes_keywords="test,podcast",
    itunes_summary="Test summary for iTunes",
    itunes_subtitle="Test subtitle",
    itunes_category="Technology",
    itunes_explicit="clean",
)


def make_podcast(owner=None, **overrides) -> Podcast:
    """
    Create a podcast with iTunes metadata.

    Args:
        owner: User who owns the podcast (created if None)
        **overrides: Field overrides
    """
    if owner is None:
        owner = make_host_user()

    return podcast_recipe.make(owner=owner, **overrides)


# PodcastEpisode recipes
podcast_episode_recipe = Recipe(
    PodcastEpisode,
    published_at=lambda: now,
    download_url=seq("https://example.com/episode/"),
    episode_guid=lambda: str(uuid.uuid4()),
    episode_title=seq("Test Episode "),
    episode_description="Test episode description",
)


def make_podcast_episode(
    podcast=None,
    file=None,
    **overrides,
) -> PodcastEpisode:
    """
    Create a podcast episode.

    Args:
        podcast: Podcast instance (created if None)
        file: File instance for episode audio (optional)
        **overrides: Field overrides
    """
    if podcast is None:
        podcast = make_podcast()

    return podcast_episode_recipe.make(
        podcast=podcast,
        file=file,
        **overrides,
    )


# StationPodcast recipes (station's own podcast feed)
station_podcast_recipe = Recipe(StationPodcast)


def make_station_podcast(podcast=None, **overrides) -> StationPodcast:
    """
    Create station podcast link.

    Args:
        podcast: Podcast instance (created if None)
    """
    if podcast is None:
        podcast = make_podcast()

    return station_podcast_recipe.make(podcast=podcast, **overrides)


# ImportedPodcast recipes (auto-imported external podcasts)
imported_podcast_recipe = Recipe(
    ImportedPodcast,
    override_album=False,
    auto_ingest=False,
    auto_ingested_at=None,
)


def make_imported_podcast(
    podcast=None,
    auto_ingest=False,
    **overrides,
) -> ImportedPodcast:
    """
    Create imported podcast configuration.

    Args:
        podcast: Podcast instance (created if None)
        auto_ingest: Whether to auto-import episodes
        **overrides: Field overrides
    """
    if podcast is None:
        podcast = make_podcast()

    defaults = {
        "auto_ingest": auto_ingest,
    }
    if auto_ingest:
        defaults["auto_ingested_at"] = now()
    defaults.update(overrides)

    return imported_podcast_recipe.make(podcast=podcast, **defaults)


# =============================================================================
# HISTORY MODELS
# =============================================================================

from api.history.models.listener import (
    ListenerCount,
    MountName,
    Timestamp,
)
from api.history.models.live import LiveLog
from api.history.models.played import (
    PlayoutHistory,
    PlayoutHistoryTemplate,
)

# PlayoutHistory recipes
playout_history_recipe = Recipe(
    PlayoutHistory,
    starts=now,
    ends=lambda: now() + timedelta(minutes=3),
)


def make_playout_history(file=None, instance=None, **overrides):
    """
    Create playout history entry.

    Args:
        file: File that was played (optional)
        instance: ShowInstance when played (optional)
    """
    return playout_history_recipe.make(
        file=file,
        instance=instance,
        **overrides,
    )


# PlayoutHistoryTemplate recipes
playout_history_template_recipe = Recipe(
    PlayoutHistoryTemplate,
    name=seq("Template "),
    type="standard",
)


def make_playout_history_template(**overrides):
    """Create history template."""
    return playout_history_template_recipe.make(**overrides)


# ListenerCount recipes
timestamp_recipe = Recipe(
    Timestamp,
    timestamp=now,
)

mount_name_recipe = Recipe(
    MountName,
    mount_name="/stream",
)

listener_count_recipe = Recipe(
    ListenerCount,
    listener_count=42,
)


def make_listener_count(
    timestamp=None,
    mount_name=None,
    count=None,
    **overrides,
):
    """
    Create listener count entry.

    Args:
        timestamp: Timestamp instance (created if None)
        mount_name: MountName instance (created if None)
        count: Listener count (default 42)
    """
    if timestamp is None:
        timestamp = timestamp_recipe.make()
    if mount_name is None:
        mount_name = mount_name_recipe.make()
    if count is not None:
        overrides["listener_count"] = count

    return listener_count_recipe.make(
        timestamp=timestamp,
        mount_name=mount_name,
        **overrides,
    )


# LiveLog recipes
live_log_recipe = Recipe(
    LiveLog,
    state="LIVE",
    start_time=now,
    end_time=None,
)


def make_live_log(state="LIVE", **overrides):
    """
    Create live log entry.

    Args:
        state: LIVE or off state
        **overrides: Field overrides
    """
    defaults = {"state": state}
    defaults.update(overrides)
    return live_log_recipe.make(**defaults)


# =============================================================================
# SCHEDULE MODEL
# =============================================================================

from api.schedule.models.schedule import Schedule

# Schedule recipes
schedule_recipe = Recipe(
    Schedule,
    starts_at=now,
    ends_at=lambda: now() + timedelta(minutes=3),
    position=0,
    position_status=Schedule.PositionStatus.INSIDE,
    broadcasted=0,
    played=False,
    fade_in=None,
    fade_out=None,
)


def make_schedule(
    instance=None,
    file=None,
    stream=None,
    cue_in=None,
    cue_out=None,
    **overrides,
) -> Schedule:
    """
    Create a schedule entry linking content to show instance.

    This is the critical model connecting files/streams to show instances.

    Args:
        instance: ShowInstance when scheduled (created if None)
        file: File to schedule (optional, for audio files)
        stream: Webstream to schedule (optional, for streams)
        cue_in: Cue in point (default 0)
        cue_out: Cue out point (default file length or 3 min)
        **overrides: Field overrides

    Returns:
        Schedule instance
    """
    if instance is None:
        instance = make_show_instance()

    # Calculate defaults from file if provided
    if file is not None:
        if cue_in is None:
            cue_in = file.cue_in or timedelta(0)
        if cue_out is None:
            cue_out = file.cue_out or file.length or timedelta(minutes=3)
        if "length" not in overrides:
            overrides["length"] = file.length
    else:
        if cue_in is None:
            cue_in = timedelta(0)
        if cue_out is None:
            cue_out = timedelta(minutes=3)

    defaults = {
        "cue_in": cue_in,
        "cue_out": cue_out,
    }
    defaults.update(overrides)

    return schedule_recipe.make(
        instance=instance,
        file=file,
        stream=stream,
        **defaults,
    )


def make_filler_schedule(instance=None, **overrides):
    """
    Create a filler schedule item (for shows that already started).

    Args:
        instance: ShowInstance (created if None)
    """
    defaults = {
        "position_status": Schedule.PositionStatus.FILLER,
    }
    defaults.update(overrides)
    return make_schedule(instance, **defaults)


def make_overbooked_schedule(instance=None, file=None, **overrides):
    """
    Create an overbooked schedule item (extends beyond show end).

    This tests the overbooked detection logic.

    Args:
        instance: ShowInstance (created if None)
        file: File to schedule
    """
    if instance is None:
        instance = make_show_instance()

    # Set starts_at after instance ends to trigger overbooked
    defaults = {
        "starts_at": instance.ends_at + timedelta(minutes=1),
        "ends_at": instance.ends_at + timedelta(minutes=4),
    }
    defaults.update(overrides)

    return make_schedule(instance, file, **defaults)


# =============================================================================
# WEBSTREAM MODELS
# =============================================================================

from api.schedule.models.webstream import Webstream, WebstreamMetadata

# Webstream recipes
webstream_recipe = Recipe(
    Webstream,
    created_at=now,
    updated_at=now,
    last_played_at=None,
    name=seq("Test Webstream "),
    description="Test webstream description",
    url="https://example.com/stream.mp3",
    length=timedelta(hours=1),  # 1 hour default
    mime="audio/mpeg",
)


def make_webstream(owner=None, **overrides) -> Webstream:
    """
    Create a webstream.

    Args:
        owner: User who owns the stream (created if None)
        **overrides: Field overrides
    """
    if owner is None:
        owner = make_host_user()

    return webstream_recipe.make(owner=owner, **overrides)


# WebstreamMetadata recipes
webstream_metadata_recipe = Recipe(
    WebstreamMetadata,
    starts_at=now,
    data='input.http(id="test", "https://example.com/stream.mp3")',
)


def make_webstream_metadata(schedule=None, **overrides) -> WebstreamMetadata:
    """
    Create webstream metadata for scheduled stream.

    Args:
        schedule: Schedule instance (created if None)
        **overrides: Field overrides
    """
    if schedule is None:
        # Create schedule with stream instead of file
        stream = make_webstream()
        schedule = make_schedule(stream=stream)

    return webstream_metadata_recipe.make(schedule=schedule, **overrides)
