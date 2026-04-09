# 📊 ДЕТАЛЬНЫЙ ОТЧЁТ: МИГРАЦИЯ API LIBRETIME НА FASTAPI

> **Дата анализа:** 2026-04-07
> **Источник:** LibreTime API v2 (Django REST Framework)
> **Цель:** FastAPI + Pydantic + SQLAlchemy с сохранением БД и внешнего интерфейса

---

## СОДЕРЖАНИЕ

1. [Система разрешений (Permissions)](#1-система-разрешений-permissions)
2. [Модуль: CORE](#2-модуль-core)
3. [Модуль: STORAGE](#3-модуль-storage)
4. [Модуль: SCHEDULE](#4-модуль-schedule)
5. [Модуль: HISTORY](#5-модуль-history)
6. [Модуль: PODCASTS](#6-модуль-podcasts)
7. [Полная карта URL](#7-полная-карта-url)
8. [Система аутентификации для FastAPI](#8-система-аутентификации-для-fastapi)
9. [Ключевые вызовы миграции](#9-ключевые-вызовы-миграции)
10. [Рекомендуемая структура FastAPI проекта](#10-рекомендуемая-структура-fastapi-проекта)

---

## 1. СИСТЕМА РАЗРЕШЕНИЙ (Permissions)

### 1.1 Кастомные Permission Classes

```python
# permissions.py

class IsAdminOrOwnUser(BasePermission):
    """Разрешение для пользователей: admin может всё, обычный пользователь - только свои данные"""
    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_superuser())

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser():
            return True
        return obj.username == request.user

class IsSystemTokenOrUser(BasePermission):
    """
    Двойная аутентификация:
    - Пользователи через стандартную Django auth
    - Сервисы (liquidsoap, др.) через Api-Key заголовок
    """
    def has_permission(self, request, view) -> bool:
        if request.user and request.user.is_authenticated:
            perm = get_permission_for_view(request, view)
            if perm == "view_apiroot":
                return True
            return request.user.has_perm(perm)
        return check_authorization_header(request)  # Api-Key проверка

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user and request.user.is_authenticated:
            perm = get_permission_for_view(request, view)
            return request.user.has_perm(perm, obj)
        return check_authorization_header(request)
```

### 1.2 Группы разрешений (permission_constants.py)

```python
# Роли: Guest(G), Host(H), Manager(P), Admin(A)

GUEST_PERMISSIONS = [
    "view_schedule", "view_show", "view_showdays", "view_showhost",
    "view_showinstance", "view_showrebroadcast", "view_file", "view_podcast",
    "view_podcastepisode", "view_playlist", "view_playlistcontent",
    "view_smartblock", "view_smartblockcontent", "view_smartblockcriteria",
    "view_webstream", "view_apiroot",
]

HOST_PERMISSIONS = GUEST_PERMISSIONS + [
    "add_file", "add_podcast", "add_podcastepisode", "add_playlist",
    "add_playlistcontent", "add_smartblock", "add_smartblockcontent",
    "add_smartblockcriteria", "add_webstream",
    # "own_" префикс для редактирования своих объектов
    "change_own_schedule", "change_own_file", "change_own_podcast",
    "change_own_podcastepisode", "change_own_playlist", ...
]

MANAGER_PERMISSIONS = GUEST_PERMISSIONS + [
    "add_show", "add_showdays", "add_showhost", "add_showinstance",
    "add_showrebroadcast", "add_file", ...
    # Полные права на изменение (без "own_" префикса)
    "change_schedule", "change_show", "change_showdays", ...
]
```

---

## 2. МОДУЛЬ: CORE (users, auth, preferences, services, workers)

### 2.1 Модели Django

#### User (`cc_subjs` table)

```python
class User(AbstractBaseUser):
    # Поля БД (db_column важен!)
    role = CharField(max_length=1, choices=Role.choices, db_column="type")
    username = CharField(unique=True, max_length=255, db_column="login")
    password = CharField(max_length=255, db_column="pass")  # MD5 hash!
    email = CharField(max_length=1024, blank=True, null=True)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)

    login_attempts = IntegerField(blank=True, null=True, db_column="login_attempts")
    last_login = DateTimeField(blank=True, null=True, db_column="lastlogin")
    last_failed_login = DateTimeField(blank=True, null=True, db_column="lastfail")

    # Контакты
    skype = CharField(max_length=1024, blank=True, null=True, db_column="skype_contact")
    jabber = CharField(max_length=1024, blank=True, null=True, db_column="jabber_contact")
    phone = CharField(max_length=1024, blank=True, null=True, db_column="cell_phone")

    class Meta:
        managed = False
        db_table = "cc_subjs"

    USERNAME_FIELD = "username"

    def set_password(self, raw_password: str | None) -> None:
        if not raw_password:
            self.set_unusable_password()
        else:
            self.password = hashlib.md5(raw_password.encode()).hexdigest()
```

#### UserToken (`cc_subjs_token`)

```python
class UserToken(models.Model):
    user = ForeignKey("core.User", on_delete=DO_NOTHING)
    action = CharField(max_length=255)
    token = CharField(unique=True, max_length=40)
    created = DateTimeField()

    class Meta:
        db_table = "cc_subjs_token"
```

#### LoginAttempt (`cc_login_attempts`)

```python
class LoginAttempt(models.Model):
    ip = CharField(primary_key=True, max_length=32)
    attempts = IntegerField(blank=True, null=True)

    class Meta:
        db_table = "cc_login_attempts"
```

#### Preference (`cc_pref`)

```python
class Preference(models.Model):
    user = ForeignKey("core.User", on_delete=CASCADE, blank=True, null=True, db_column="subjid")
    key = CharField(max_length=255, unique=True, blank=True, null=True, db_column="keystr")
    value = TextField(blank=True, null=True, db_column="valstr")

    class Meta:
        db_table = "cc_pref"
        unique_together = (("user", "key"),)
```

#### ServiceRegister (`cc_service_register`)

```python
class ServiceRegister(models.Model):
    name = CharField(primary_key=True, max_length=32)
    ip = CharField(max_length=45)

    class Meta:
        db_table = "cc_service_register"
```

#### ThirdPartyTrackReference

```python
class ThirdPartyTrackReference(models.Model):
    service = CharField(max_length=256)
    foreign_id = CharField(unique=True, max_length=256, blank=True, null=True)
    file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True)
    upload_time = DateTimeField(blank=True, null=True)
    status = CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = "third_party_track_references"
```

#### CeleryTask

```python
class CeleryTask(models.Model):
    task_id = CharField(max_length=256)
    track_reference = ForeignKey("core.ThirdPartyTrackReference", on_delete=DO_NOTHING)
    name = CharField(max_length=256, blank=True, null=True)
    dispatch_time = DateTimeField(blank=True, null=True)
    status = CharField(max_length=256)

    class Meta:
        db_table = "celery_tasks"
```

### 2.2 Сериализаторы DRF → Pydantic Models

```python
# Pydantic модели для FastAPI

class UserBase(BaseModel):
    role: str  # G, H, P, A
    username: str
    email: Optional[str] = None
    first_name: str
    last_name: str
    login_attempts: Optional[int] = None
    last_login: Optional[datetime] = None
    last_failed_login: Optional[datetime] = None
    skype: Optional[str] = None
    jabber: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    skype: Optional[str] = None
    jabber: Optional[str] = None
    phone: Optional[str] = None

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# Stream Preferences (read-only, вычисляемые из Preference)
class StreamPreferences(BaseModel):
    input_fade_transition: float
    message_format: int  # 0, 1, 2
    message_offline: str
    replay_gain_enabled: bool
    replay_gain_offset: float

class StreamState(BaseModel):
    input_main_connected: bool
    input_main_streaming: bool
    input_show_connected: bool
    input_show_streaming: bool
    schedule_streaming: bool

class InfoResponse(BaseModel):
    station_name: str

class VersionResponse(BaseModel):
    api_version: str
```

### 2.3 ViewSets → FastAPI Endpoints

```python
# Router core

# ModelViewSet endpoints (стандартные CRUD)
@router.get("/users", response_model=List[UserResponse])
@router.post("/users", response_model=UserResponse)
@router.get("/users/{id}", response_model=UserResponse)
@router.put("/users/{id}", response_model=UserResponse)
@router.patch("/users/{id}", response_model=UserResponse)
@router.delete("/users/{id}")

# Подобные endpoints для:
# - /login-attempts
# - /preferences
# - /service-registers
# - /user-tokens
# - /celery-tasks
# - /third-party-track-references

# APIView endpoints (кастомные)
@router.get("/info", response_model=InfoResponse)  # AllowAny
@router.get("/version", response_model=VersionResponse)  # AllowAny
@router.get("/stream/preferences", response_model=StreamPreferences)  # IsSystemTokenOrUser
@router.get("/stream/state", response_model=StreamState)  # IsSystemTokenOrUser
```

### 2.4 Permissions для Core

| Endpoint | Permission |
|----------|------------|
| /users | IsAdminOrOwnUser |
| /login-attempts | IsSystemTokenOrUser (по умолчанию) |
| /preferences | IsSystemTokenOrUser |
| /service-registers | IsSystemTokenOrUser |
| /user-tokens | IsSystemTokenOrUser |
| /celery-tasks | IsSystemTokenOrUser |
| /third-party-track-references | IsSystemTokenOrUser |
| /info | AllowAny |
| /version | AllowAny |
| /stream/* | IsSystemTokenOrUser |

---

## 3. МОДУЛЬ: STORAGE (files, libraries)

### 3.1 Модели Django

#### File (`cc_files` table) — ОГРОМНАЯ МОДЕЛЬ

```python
class File(models.Model):
    class Meta:
        db_table = "cc_files"
        permissions = (
            ("change_own_file", "Change the files where they are the owner"),
            ("delete_own_file", "Delete the files where they are the owner"),
        )

    class ImportStatus(IntegerChoices):
        SUCCESS = 0, "Success"
        PENDING = 1, "Pending"
        FAILED = 2, "Failed"

    # Связи
    library = ForeignKey("storage.Library", DO_NOTHING, blank=True, null=True, db_column="track_type_id")
    owner = ForeignKey("core.User", DO_NOTHING, blank=True, null=True)
    edited_by = ForeignKey("core.User", DO_NOTHING, blank=True, null=True, related_name="edited_files", db_column="editedby")

    # Статус
    import_status = IntegerField(choices=ImportStatus.choices, default=ImportStatus.PENDING)

    # Файл
    filepath = TextField(blank=True, null=True)
    size = IntegerField(db_column="filesize")
    exists = BooleanField(blank=True, null=True, db_column="file_exists")
    mime = CharField(max_length=255)
    md5 = CharField(max_length=32, blank=True, null=True)

    # Флаги
    hidden = BooleanField(blank=True, null=True)
    accessed = IntegerField(db_column="currentlyaccessing")
    scheduled = BooleanField(blank=True, null=True, db_column="is_scheduled")
    part_of_list = BooleanField(blank=True, null=True, db_column="is_playlist")

    # Временные метки
    created_at = DateTimeField(blank=True, null=True, db_column="utime")
    updated_at = DateTimeField(blank=True, null=True, db_column="mtime")
    last_played_at = DateTimeField(blank=True, null=True, db_column="lptime")

    # Аудио параметры
    bit_rate = IntegerField(blank=True, null=True)
    sample_rate = IntegerField(blank=True, null=True)
    format = CharField(max_length=128, blank=True, null=True)
    channels = IntegerField(blank=True, null=True)
    length = DurationField(blank=True, null=True)
    bpm = IntegerField(blank=True, null=True)
    replay_gain = DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    cue_in = DurationField(blank=True, null=True, db_column="cuein")
    cue_out = DurationField(blank=True, null=True, db_column="cueout")

    # Метаданные (очень много полей!)
    name = CharField(max_length=255)
    description = CharField(max_length=512, blank=True, null=True)
    artwork = CharField(max_length=512, blank=True, null=True)
    artist_name = CharField(max_length=512, blank=True, null=True)
    artist_url = CharField(max_length=512, blank=True, null=True)
    original_artist = CharField(max_length=512, blank=True, null=True)
    album_title = CharField(max_length=512, blank=True, null=True)
    track_title = CharField(max_length=512, blank=True, null=True)
    genre = CharField(max_length=64, blank=True, null=True)
    mood = CharField(max_length=64, blank=True, null=True)
    date = CharField(max_length=16, blank=True, null=True, db_column="year")
    track_number = IntegerField(blank=True, null=True)
    disc_number = CharField(max_length=8, blank=True, null=True)
    comment = TextField(blank=True, null=True, db_column="comments")
    language = CharField(max_length=512, blank=True, null=True)
    label = CharField(max_length=512, blank=True, null=True)
    copyright = CharField(max_length=512, blank=True, null=True)
    composer = CharField(max_length=512, blank=True, null=True)
    conductor = CharField(max_length=512, blank=True, null=True)
    orchestra = CharField(max_length=512, blank=True, null=True)
    encoder = CharField(max_length=64, blank=True, null=True)
    encoded_by = CharField(max_length=255, blank=True, null=True)
    isrc = CharField(max_length=512, blank=True, null=True, db_column="isrc_number")
    lyrics = TextField(blank=True, null=True)
    lyricist = CharField(max_length=512, blank=True, null=True)
    original_lyricist = CharField(max_length=512, blank=True, null=True)
    subject = CharField(max_length=512, blank=True, null=True)
    contributor = CharField(max_length=512, blank=True, null=True)
    rating = CharField(max_length=8, blank=True, null=True)
    url = CharField(max_length=1024, blank=True, null=True)
    info_url = CharField(max_length=512, blank=True, null=True)
    audio_source_url = CharField(max_length=512, blank=True, null=True)
    buy_this_url = CharField(max_length=512, blank=True, null=True)
    catalog_number = CharField(max_length=512, blank=True, null=True)
    radio_station_name = CharField(max_length=512, blank=True, null=True)
    radio_station_url = CharField(max_length=512, blank=True, null=True)
    report_datetime = CharField(max_length=32, blank=True, null=True)
    report_location = CharField(max_length=512, blank=True, null=True)
    report_organization = CharField(max_length=512, blank=True, null=True)
```

#### Library (`cc_track_types`)

```python
class Library(models.Model):
    class Meta:
        db_table = "cc_track_types"

    name = CharField(max_length=255, blank=True, null=True, db_column="type_name")
    code = CharField(max_length=16, unique=True)
    description = CharField(max_length=255, blank=True, null=True)
    enabled = BooleanField(blank=True, default=True, db_column="visibility")
    analyze_cue_points = BooleanField(blank=True, default=True, db_column="analyze_cue_points")
    id = AutoField(primary_key=True)
```

### 3.2 Сериализаторы → Pydantic

```python
class FileBase(BaseModel):
    # Все ~50 полей File модели
    library_id: Optional[int] = None
    owner_id: Optional[int] = None
    import_status: int = 1  # PENDING
    filepath: Optional[str] = None
    size: int
    exists: Optional[bool] = None
    mime: str
    md5: Optional[str] = None
    # ... все остальные поля

class FileResponse(FileBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_played_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LibraryBase(BaseModel):
    name: Optional[str] = None
    code: str
    description: Optional[str] = None
    enabled: bool = True
    analyze_cue_points: bool = True

class LibraryResponse(LibraryBase):
    id: int

    class Config:
        from_attributes = True
```

### 3.3 ViewSets → FastAPI

```python
# FileViewSet имеет КАСТОМНЫЕ actions!

@router.get("/files", response_model=List[FileResponse])
@router.post("/files", response_model=FileResponse)
@router.get("/files/{id}", response_model=FileResponse)
@router.put("/files/{id}", response_model=FileResponse)
@router.patch("/files/{id}", response_model=FileResponse)
@router.delete("/files/{id}")

# КАСТОМНЫЙ ACTION
@router.get("/files/{id}/download")
def download_file(id: int):
    """Возвращает X-Accel-Redirect для nginx"""
    instance = get_file(id)
    redirect_uri = filepath_to_uri(os.path.join("/api/_media", instance.filepath))
    return Response(headers={"X-Accel-Redirect": redirect_uri})

# Фильтры для FileViewSet
filterset_fields = ("md5", "genre")

@router.get("/libraries", response_model=List[LibraryResponse])
# ... стандартные CRUD
```

### 3.4 Permissions Storage

| Endpoint | Permission |
|----------|------------|
| /files | IsSystemTokenOrUser (view_file/change_own_file/delete_own_file) |
| /libraries | IsSystemTokenOrUser |

---

## 4. МОДУЛЬ: SCHEDULE (shows, playlists, smart blocks, webstreams, schedule)

### 4.1 Модели Django

#### Show (`cc_show`)

```python
class Show(models.Model):
    class Meta:
        db_table = "cc_show"

    name = CharField(max_length=255)
    description = CharField(max_length=8192, blank=True, null=True)
    genre = CharField(max_length=255, blank=True, null=True)
    url = CharField(max_length=255, blank=True, null=True)
    image = CharField(max_length=255, blank=True, null=True, db_column="image_path")
    foreground_color = CharField(max_length=6, blank=True, null=True, db_column="color")
    background_color = CharField(max_length=6, blank=True, null=True)

    # Live streaming auth
    live_auth_registered = BooleanField(default=False, blank=True, null=True, db_column="live_stream_using_airtime_auth")
    live_auth_custom = BooleanField(default=False, blank=True, null=True, db_column="live_stream_using_custom_auth")
    live_auth_custom_user = CharField(max_length=255, blank=True, null=True, db_column="live_stream_user")
    live_auth_custom_password = CharField(max_length=255, blank=True, null=True, db_column="live_stream_pass")

    # Связи
    linked = BooleanField()
    linkable = BooleanField(db_column="is_linkable")
    auto_playlist = ForeignKey("schedule.Playlist", DO_NOTHING, blank=True, null=True, db_column="autoplaylist_id")
    auto_playlist_enabled = BooleanField(db_column="has_autoplaylist")
    auto_playlist_repeat = BooleanField(db_column="autoplaylist_repeat")
    intro_playlist = ForeignKey("schedule.Playlist", DO_NOTHING, blank=True, null=True,
                                 db_column="intro_playlist_id", related_name="intro_playlist")
    override_intro_playlist = BooleanField(db_column="override_intro_playlist")
    outro_playlist = ForeignKey("schedule.Playlist", DO_NOTHING, blank=True, null=True,
                                db_column="outro_playlist_id", related_name="outro_playlist")
    override_outro_playlist = BooleanField(db_column="override_outro_playlist")

    hosts = ManyToManyField("core.User", through="ShowHost")
```

#### ShowHost (`cc_show_hosts`)

```python
class ShowHost(models.Model):
    class Meta:
        db_table = "cc_show_hosts"

    show = ForeignKey("schedule.Show", on_delete=DO_NOTHING)
    user = ForeignKey("core.User", on_delete=DO_NOTHING, db_column="subjs_id")
```

#### ShowDays (`cc_show_days`)

```python
class ShowDays(models.Model):
    class Meta:
        db_table = "cc_show_days"

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

    show = ForeignKey("schedule.Show", on_delete=DO_NOTHING)
    first_show_on = DateField(db_column="first_show")
    last_show_on = DateField(blank=True, null=True, db_column="last_show")
    start_time = TimeField()
    timezone = CharField(max_length=1024)
    duration = CharField(max_length=1024)
    record_enabled = SmallIntegerField(choices=Record.choices, default=Record.NO, blank=True, null=True, db_column="record")
    week_day = SmallIntegerField(choices=WeekDay.choices, blank=True, null=True, db_column="day")
    repeat_kind = SmallIntegerField(choices=RepeatKind.choices, db_column="repeat_type")
    repeat_next_on = DateField(blank=True, null=True, db_column="next_pop_date")
```

#### ShowInstance (`cc_show_instances`)

```python
class ShowInstance(models.Model):
    class Meta:
        db_table = "cc_show_instances"

    created_at = DateTimeField(db_column="created")
    show = ForeignKey("schedule.Show", on_delete=DO_NOTHING)
    instance = ForeignKey("self", on_delete=DO_NOTHING, blank=True, null=True)  # Self-referential
    starts_at = DateTimeField(db_column="starts")
    ends_at = DateTimeField(db_column="ends")
    filled_time = DurationField(blank=True, null=True, db_column="time_filled")
    last_scheduled_at = DateTimeField(blank=True, null=True, db_column="last_scheduled")
    description = CharField(max_length=8192, blank=True, null=True)
    modified = BooleanField(db_column="modified_instance")
    rebroadcast = SmallIntegerField(blank=True, null=True)
    auto_playlist_built = BooleanField(db_column="autoplaylist_built")
    record_enabled = SmallIntegerField(choices=Record.choices, default=Record.NO, blank=True, null=True, db_column="record")
    record_file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True, db_column="file_id")
```

#### ShowRebroadcast (`cc_show_rebroadcast`)

```python
class ShowRebroadcast(models.Model):
    class Meta:
        db_table = "cc_show_rebroadcast"

    show = ForeignKey("schedule.Show", on_delete=DO_NOTHING)
    day_offset = CharField(max_length=1024)
    start_time = TimeField()
```

#### Playlist (`cc_playlist`)

```python
class Playlist(models.Model):
    class Meta:
        db_table = "cc_playlist"

    created_at = DateTimeField(blank=True, null=True, db_column="utime")
    updated_at = DateTimeField(blank=True, null=True, db_column="mtime")
    name = CharField(max_length=255)
    description = CharField(max_length=512, blank=True, null=True)
    length = DurationField(blank=True, null=True)
    owner = ForeignKey("core.User", on_delete=DO_NOTHING, blank=True, null=True, db_column="creator_id")
```

#### PlaylistContent (`cc_playlistcontents`)

```python
class PlaylistContent(models.Model):
    class Meta:
        db_table = "cc_playlistcontents"

    class Kind(IntegerChoices):
        FILE = 0, "File"
        STREAM = 1, "Stream"
        BLOCK = 2, "Block"

    playlist = ForeignKey("schedule.Playlist", on_delete=DO_NOTHING, blank=True, null=True)
    kind = SmallIntegerField(choices=Kind.choices, db_column="type")
    file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True)
    stream = ForeignKey("schedule.Webstream", on_delete=DO_NOTHING, blank=True, null=True)
    block = ForeignKey("schedule.SmartBlock", on_delete=DO_NOTHING, blank=True, null=True)
    position = IntegerField(blank=True, null=True)
    offset = FloatField(db_column="trackoffset")
    length = DurationField(blank=True, null=True, db_column="cliplength")
    cue_in = DurationField(blank=True, null=True, db_column="cuein")
    cue_out = DurationField(blank=True, null=True, db_column="cueout")
    fade_in = TimeField(blank=True, null=True, db_column="fadein")
    fade_out = TimeField(blank=True, null=True, db_column="fadeout")
```

#### SmartBlock (`cc_block`)

```python
class SmartBlock(models.Model):
    class Meta:
        db_table = "cc_block"
        permissions = (
            ("change_own_smartblock", "Change the smartblocks where they are the owner"),
            ("delete_own_smartblock", "Delete the smartblocks where they are the owner"),
        )

    class Kind(TextChoices):
        STATIC = "static", "Static"
        DYNAMIC = "dynamic", "Dynamic"

    created_at = DateTimeField(blank=True, null=True, db_column="utime")
    updated_at = DateTimeField(blank=True, null=True, db_column="mtime")
    name = CharField(max_length=255)
    description = CharField(max_length=512, blank=True, null=True)
    length = DurationField(blank=True, null=True)
    kind = CharField(choices=Kind.choices, default=Kind.DYNAMIC, max_length=7, blank=True, null=True, db_column="type")
    owner = ForeignKey("core.User", on_delete=DO_NOTHING, blank=True, null=True, db_column="creator_id")
```

#### SmartBlockContent (`cc_blockcontents`)

```python
class SmartBlockContent(models.Model):
    class Meta:
        db_table = "cc_blockcontents"
        permissions = (...)  # change_own_smartblockcontent, delete_own_smartblockcontent

    block = ForeignKey("schedule.SmartBlock", on_delete=DO_NOTHING, blank=True, null=True)
    file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True)
    position = IntegerField(blank=True, null=True)
    offset = FloatField(db_column="trackoffset")
    length = DurationField(blank=True, null=True, db_column="cliplength")
    cue_in = DurationField(blank=True, null=True, db_column="cuein")
    cue_out = DurationField(blank=True, null=True, db_column="cueout")
    fade_in = TimeField(blank=True, null=True, db_column="fadein")
    fade_out = TimeField(blank=True, null=True, db_column="fadeout")
```

#### SmartBlockCriteria (`cc_blockcriteria`)

```python
class SmartBlockCriteria(models.Model):
    class Meta:
        db_table = "cc_blockcriteria"
        permissions = (...)  # change_own_smartblockcriteria, delete_own_smartblockcriteria

    block = ForeignKey("schedule.SmartBlock", on_delete=DO_NOTHING)
    group = IntegerField(blank=True, null=True, db_column="criteriagroup")
    criteria = CharField(max_length=32)
    condition = CharField(max_length=16, db_column="modifier")
    value = CharField(max_length=512)
    extra = CharField(max_length=512, blank=True, null=True)
```

#### Webstream (`cc_webstream`)

```python
class Webstream(models.Model):
    class Meta:
        db_table = "cc_webstream"
        permissions = (
            ("change_own_webstream", "Change the webstreams where they are the owner"),
            ("delete_own_webstream", "Delete the webstreams where they are the owner"),
        )

    created_at = DateTimeField(db_column="utime")
    updated_at = DateTimeField(db_column="mtime")
    last_played_at = DateTimeField(blank=True, null=True, db_column="lptime")
    name = CharField(max_length=255)
    description = CharField(max_length=255)
    url = CharField(max_length=512)
    length = DurationField()
    mime = CharField(max_length=1024, blank=True, null=True)
    owner = ForeignKey("core.User", on_delete=DO_NOTHING, blank=True, null=True, db_column="creator_id")
```

#### WebstreamMetadata (`cc_webstream_metadata`)

```python
class WebstreamMetadata(models.Model):
    class Meta:
        db_table = "cc_webstream_metadata"

    schedule = ForeignKey("schedule.Schedule", on_delete=DO_NOTHING, db_column="instance_id")
    starts_at = DateTimeField(db_column="start_time")
    data = CharField(max_length=1024, db_column="liquidsoap_data")
```

#### Schedule (`cc_schedule`) — КЛЮЧЕВАЯ МОДЕЛЬ

```python
class Schedule(models.Model):
    class Meta:
        db_table = "cc_schedule"
        permissions = (
            ("change_own_schedule", "Change the content on their shows"),
            ("delete_own_schedule", "Delete the content on their shows"),
        )

    class PositionStatus(IntegerChoices):
        FILLER = -1, "Filler"
        OUTSIDE = 0, "Outside"
        INSIDE = 1, "Inside"
        BOUNDARY = 2, "Boundary"

    starts_at = DateTimeField(db_column="starts")
    ends_at = DateTimeField(db_column="ends")
    instance = ForeignKey("schedule.ShowInstance", on_delete=DO_NOTHING)
    file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True)
    stream = ForeignKey("schedule.Webstream", on_delete=DO_NOTHING, blank=True, null=True)
    length = DurationField(blank=True, null=True, db_column="clip_length")
    fade_in = TimeField(blank=True, null=True)
    fade_out = TimeField(blank=True, null=True)
    cue_in = DurationField()
    cue_out = DurationField()
    position = IntegerField()
    position_status = SmallIntegerField(choices=PositionStatus.choices, default=PositionStatus.INSIDE, db_column="playout_status")
    broadcasted = SmallIntegerField()
    played = BooleanField(blank=True, null=True, db_column="media_item_played")

    # Методы для вычисляемых полей (используются в ReadScheduleSerializer)
    def get_cue_out(self) -> timedelta:
        """Возвращает cue_out с учётом границ show instance"""
        if self.starts_at < self.instance.ends_at and self.instance.ends_at < self.ends_at:
            return self.instance.ends_at - self.starts_at
        return self.cue_out

    def get_ends_at(self) -> datetime:
        """Возвращает ends_at с учётом границ show instance"""
        if self.instance.ends_at < self.ends_at:
            return self.instance.ends_at
        return self.ends_at

    @staticmethod
    def is_file_scheduled_in_the_future(file_id: str) -> bool:
        return bool(Schedule.objects.filter(file_id=file_id, ends_at__gt=now()).count())
```

### 4.2 Сериализаторы → Pydantic

```python
# ВАЖНО: Schedule имеет ДВА сериализатора (Read/Write)

class ShowBase(BaseModel):
    name: str
    description: Optional[str] = None
    genre: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    foreground_color: Optional[str] = None
    background_color: Optional[str] = None
    live_enabled: bool  # property
    linked: bool
    linkable: bool
    auto_playlist_id: Optional[int] = None
    auto_playlist_enabled: bool
    auto_playlist_repeat: bool
    intro_playlist_id: Optional[int] = None
    override_intro_playlist: bool
    outro_playlist_id: Optional[int] = None
    override_outro_playlist: bool

class ShowResponse(ShowBase):
    id: int

    class Config:
        from_attributes = True

# Schedule - ДВА сериализатора!
class ScheduleRead(BaseModel):
    """Используется для GET запросов - с вычисляемыми полями"""
    id: int
    starts_at: datetime
    ends_at: datetime
    instance_id: int
    file_id: Optional[int] = None
    stream_id: Optional[int] = None
    length: Optional[timedelta] = None
    fade_in: Optional[time] = None
    fade_out: Optional[time] = None
    cue_in: timedelta
    cue_out: timedelta
    # ВЫЧИСЛЯЕМЫЕ ПОЛЯ (read_only)
    cue_out_calculated: timedelta  # source="get_cue_out"
    ends_at_calculated: datetime   # source="get_ends_at"
    position: int
    position_status: int
    broadcasted: int
    played: Optional[bool] = None

class ScheduleWrite(BaseModel):
    """Используется для POST/PUT/PATCH - без вычисляемых полей"""
    starts_at: datetime
    ends_at: datetime
    instance_id: int
    file_id: Optional[int] = None
    stream_id: Optional[int] = None
    length: Optional[timedelta] = None
    fade_in: Optional[time] = None
    fade_out: Optional[time] = None
    cue_in: timedelta
    cue_out: timedelta
    position: int
    position_status: int = 1  # INSIDE
    broadcasted: int
    played: Optional[bool] = None
```

### 4.3 ScheduleViewSet — ОСОБЫЙ случай

```python
# Использует ReadWriteSerializerMixin!
class ScheduleViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    read_serializer_class = ReadScheduleSerializer   # для GET
    write_serializer_class = WriteScheduleSerializer  # для POST/PUT/PATCH
    filterset_class = ScheduleFilter
    model_permission_name = "schedule"

# ScheduleFilter (django-filter)
class ScheduleFilter(FilterSet):
    starts = DateTimeFromToRangeFilter(field_name="starts_at")
    ends = DateTimeFromToRangeFilter(field_name="ends_at")
    position_status = NumberFilter()
    broadcasted = NumberFilter()
    overbooked = BooleanFilter(method="overbooked_filter")

    def overbooked_filter(self, queryset, name, value):
        if value:
            return queryset.filter(starts_at__gte=F("instance__ends_at"))
        return queryset.filter(starts_at__lt=F("instance__ends_at"))
```

### 4.4 Endpoints Schedule

```python
# Все ModelViewSet CRUD операции:

# Shows
@router.get("/shows")
@router.post("/shows")
@router.get("/shows/{id}")
@router.put("/shows/{id}")
@router.patch("/shows/{id}")
@router.delete("/shows/{id}")

# ShowDays, ShowHosts, ShowInstances, ShowRebroadcasts
# Playlists, PlaylistContents
# SmartBlocks, SmartBlockContents, SmartBlockCriteria
# Webstreams, WebstreamMetadata

# Schedule - с фильтрами
@router.get("/schedule")  # поддерживает ?starts_after=&starts_before=&overbooked=
@router.post("/schedule")
@router.get("/schedule/{id}")
@router.put("/schedule/{id}")
@router.patch("/schedule/{id}")
@router.delete("/schedule/{id}")
```

---

## 5. МОДУЛЬ: HISTORY (listeners, live, played)

### 5.1 Модели

```python
# ListenerCount, MountName, Timestamp
class MountName(models.Model):
    mount_name = CharField(max_length=1024)
    class Meta:
        db_table = "cc_mount_name"

class Timestamp(models.Model):
    timestamp = DateTimeField()
    class Meta:
        db_table = "cc_timestamp"

class ListenerCount(models.Model):
    timestamp = ForeignKey("history.Timestamp", on_delete=DO_NOTHING)
    mount_name = ForeignKey("history.MountName", on_delete=DO_NOTHING)
    listener_count = IntegerField()
    class Meta:
        db_table = "cc_listener_count"

# LiveLog
class LiveLog(models.Model):
    state = CharField(max_length=32)
    start_time = DateTimeField()
    end_time = DateTimeField(blank=True, null=True)
    class Meta:
        db_table = "cc_live_log"

# PlayoutHistory
class PlayoutHistory(models.Model):
    file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True)
    starts = DateTimeField()
    ends = DateTimeField(blank=True, null=True)
    instance = ForeignKey("schedule.ShowInstance", on_delete=DO_NOTHING, blank=True, null=True)
    class Meta:
        db_table = "cc_playout_history"

class PlayoutHistoryMetadata(models.Model):
    history = ForeignKey("history.PlayoutHistory", on_delete=DO_NOTHING)
    key = CharField(max_length=128)
    value = CharField(max_length=128)
    class Meta:
        db_table = "cc_playout_history_metadata"

class PlayoutHistoryTemplate(models.Model):
    name = CharField(max_length=128)
    type = CharField(max_length=35)
    class Meta:
        db_table = "cc_playout_history_template"

class PlayoutHistoryTemplateField(models.Model):
    template = ForeignKey("history.PlayoutHistoryTemplate", on_delete=DO_NOTHING)
    name = CharField(max_length=128)
    label = CharField(max_length=128)
    type = CharField(max_length=128)
    is_file_md = BooleanField()
    position = IntegerField()
    class Meta:
        db_table = "cc_playout_history_template_field"
```

### 5.2 Endpoints History

```python
# Стандартные CRUD для всех:
# /listener-counts
# /live-logs
# /mount-names
# /playout-history
# /playout-history-metadata
# /playout-history-templates
# /playout-history-template-fields
# /timestamps
```

---

## 6. МОДУЛЬ: PODCASTS

### 6.1 Модели

```python
class Podcast(models.Model):
    url = CharField(max_length=4096)
    title = CharField(max_length=4096)
    creator = CharField(max_length=4096, blank=True, null=True)
    description = CharField(max_length=4096, blank=True, null=True)
    language = CharField(max_length=4096, blank=True, null=True)
    copyright = CharField(max_length=4096, blank=True, null=True)
    link = CharField(max_length=4096, blank=True, null=True)

    # iTunes поля
    itunes_author = CharField(max_length=4096, blank=True, null=True)
    itunes_keywords = CharField(max_length=4096, blank=True, null=True)
    itunes_summary = CharField(max_length=4096, blank=True, null=True)
    itunes_subtitle = CharField(max_length=4096, blank=True, null=True)
    itunes_category = CharField(max_length=4096, blank=True, null=True)
    itunes_explicit = CharField(max_length=4096, blank=True, null=True)

    owner = ForeignKey("core.User", on_delete=DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = "podcast"
        permissions = [
            ("change_own_podcast", "Change the podcasts where they are the owner"),
            ("delete_own_podcast", "Delete the podcasts where they are the owner"),
        ]

class PodcastEpisode(models.Model):
    podcast = ForeignKey("podcasts.Podcast", on_delete=DO_NOTHING)
    file = ForeignKey("storage.File", on_delete=DO_NOTHING, blank=True, null=True)
    published_at = DateTimeField(db_column="publication_date")
    download_url = CharField(max_length=4096)
    episode_guid = CharField(max_length=4096)
    episode_title = CharField(max_length=4096)
    episode_description = TextField()

    class Meta:
        db_table = "podcast_episodes"
        permissions = [...]  # change_own_podcastepisode, delete_own_podcastepisode

class StationPodcast(models.Model):
    podcast = ForeignKey("podcasts.Podcast", on_delete=DO_NOTHING)
    class Meta:
        db_table = "station_podcast"

class ImportedPodcast(models.Model):
    podcast = ForeignKey("podcasts.Podcast", on_delete=DO_NOTHING)
    override_album = BooleanField(db_column="album_override")
    auto_ingest = BooleanField()
    auto_ingested_at = DateTimeField(blank=True, null=True, db_column="auto_ingest_timestamp")
    class Meta:
        db_table = "imported_podcast"
```

### 6.2 Endpoints Podcasts

```python
# /podcast-episodes
# /podcasts
# /station-podcasts
# /imported-podcasts
```

---

## 7. ПОЛНАЯ КАРТА URL

```
api/v2/
├── core/
│   ├── login-attempts
│   ├── preferences
│   ├── service-registers
│   ├── users
│   ├── user-tokens
│   ├── celery-tasks
│   ├── third-party-track-references
│   ├── info              # GET only
│   ├── version           # GET only
│   ├── stream/preferences # GET only
│   └── stream/state      # GET only
├── storage/
│   ├── files
│   │   └── {id}/download  # custom action
│   └── libraries
├── schedule/
│   ├── shows
│   ├── show-days
│   ├── show-hosts
│   ├── show-instances
│   ├── show-rebroadcasts
│   ├── playlists
│   ├── playlist-contents
│   ├── smart-blocks
│   ├── smart-block-contents
│   ├── smart-block-criteria
│   ├── webstreams
│   ├── webstream-metadata
│   └── schedule          # с фильтрами
├── history/
│   ├── listener-counts
│   ├── live-logs
│   ├── mount-names
│   ├── playout-history
│   ├── playout-history-metadata
│   ├── playout-history-templates
│   ├── playout-history-template-fields
│   └── timestamps
└── podcasts/
    ├── podcast-episodes
    ├── podcasts
    ├── station-podcasts
    └── imported-podcasts
```

---

## 8. СИСТЕМА АУТЕНТИФИКАЦИИ ДЛЯ FASTAPI

```python
# dependencies.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка Django session auth или API-Key"""
    token = credentials.credentials

    # Проверка API-Key
    if credentials.scheme == "Api-Key":
        if compare_digest(token, settings.CONFIG.general.api_key):
            return SystemUser()  # Специальный объект для сервисов
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Проверка Django session (через заголовок Cookie)
    # Или JWT если будем мигрировать на него
    user = await verify_django_session(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

def check_permission(user, permission: str, obj=None):
    """Проверка разрешения Django-style"""
    if user.is_superuser():
        return True
    if not permission:
        return False
    return user.has_perm(permission, obj)

# Permission dependencies
def require_permission(permission: str):
    async def permission_checker(user: User = Depends(get_current_user)):
        if not check_permission(user, permission):
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        return user
    return permission_checker
```

---

## 9. КЛЮЧЕВЫЕ ВЫЗОВЫ МИГРАЦИИ

### 9.1 Сложности

| Проблема | Решение |
|----------|---------|
| 50+ полей в File модели | Использовать `**kwargs` или разбить на подмодели |
| MD5 пароли (небезопасно) | Постепенная миграция на bcrypt при логине |
| Read/Write сериализаторы | FastAPI response_model + разные input schemas |
| Django ORM relations | SQLAlchemy relationships или raw SQL |
| Managed=False модели | SQLAlchemy Table() с autoload или ручное описание |
| Permission system | Собственная реализация или CASL/Casbin |

### 9.2 Таблицы БД (managed=False)

Все модели используют `managed = False` — Django НЕ управляет схемой. Для FastAPI/SQLAlchemy:

```python
# SQLAlchemy approach
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import mapper

metadata = MetaData()

cc_files = Table(
    "cc_files", metadata,
    Column("id", Integer, primary_key=True),
    Column("track_type_id", Integer, ForeignKey("cc_track_types.id")),
    Column("filesize", Integer),
    # ... все 50+ полей
    autoload_with=engine  # Автозагрузка схемы
)
```

---

## 10. РЕКОМЕНДУЕМАЯ СТРУКТУРА FASTAPI ПРОЕКТА

```
app/
├── api/
│   ├── __init__.py
│   ├── dependencies.py      # Auth, permissions
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas/             # Pydantic схемы
│   │   ├── core.py
│   │   ├── storage.py
│   │   ├── schedule.py
│   │   ├── history.py
│   │   └── podcasts.py
│   └── routers/
│       ├── core.py
│       ├── storage.py
│       ├── schedule.py
│       ├── history.py
│       └── podcasts.py
├── core/
│   ├── config.py            # Pydantic Settings
│   ├── security.py          # Password hashing, tokens
│   └── permissions.py       # Permission system
├── db/
│   ├── base.py              # SQLAlchemy base
│   └── session.py           # Async session
└── main.py                  # FastAPI app
```

---

*Составлено для миграции LibreTime API с Django REST Framework на FastAPI*
