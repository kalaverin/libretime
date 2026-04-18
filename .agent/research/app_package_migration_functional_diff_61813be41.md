# Functional diff report: `61813be41` → `HEAD` (mapped `*/libretime_*` → `app/*/<short_pkg>/`)

Scope: logic and behavior only. Tests ignored. Import path renames from package move omitted unless behavior changes. Type hints, Python 3.10 syntax, and pure style-only edits omitted unless they affect runtime.

Full line-by-line coverage of all ~182 changed non-test files is not practical in one document; identical files and purely mechanical edits are summarized. Where line numbers refer to **current** (`HEAD`) paths under `app/`.

---

## 1. Byte-identical package files (34)

No logic change. Includes e.g. `app/analyzer/analyzer/__init__.py`, `app/api-client/api_client/py.typed`, `app/api/api/__init__.py`, `_constants.py`, `core/models/role.py`, various `__init__.py`, `legacy/migrations/sql/*`, `api/_fixtures/song.mp3`, several playout `liquidsoap` assets (`1.4/ls_script.liq`, `README.md`, `models.py`, `utils.py`, `mime.types`, some `__init__.py`), `worker/worker/__init__.py`, etc.

---

## 2. New artifacts in `HEAD` only (no old path)

### API (`app/api/api/`)

| File | Behavior |
|------|----------|
| `middlewares.py` | `RequestLoggingMiddleware`: if `response.exception` is set, logs **fatal** with method, path, status, headers, **response body** (risk of secrets in logs). See lines ~12–27. |
| `fields.py` | `TimezoneAwareDateTimeField`: naive DB datetimes → UTC-aware; strings parsed; naive values made aware on save. Lines ~13–50. |
| `serializers.py` | Mass-assignment protection (`id`, `owner`, `created_at`); `StrictSerializer` rejects unknown fields; `TimestampSerializer` sets timestamps; `SecureModelSerializer` combines. Lines ~59–216. |
| `mixins/ownership.py` | `perform_create` auto-assigns `owner` only for **session** users, not API-Key. Lines ~26–53. |
| `storage/validators.py` | Path traversal, absolute paths, null bytes, Unicode “junk” for filenames. Lines ~17–100. |
| `validators/url.py` | SSRF-oriented URL validation (schemes, internal IPs, metadata endpoints). |
| `validators/xss.py` | Stored XSS sanitization for text. |
| `validators/fields.py` | Shared field validators (length, FK, duration, duplicates, etc.). |
| `validators/race_conditions.py` | Race / duplicate checks. |

`storage/models/file.py` also adds explicit `Meta.permissions` for `change_own_file` / `delete_own_file` on the unmanaged `File` model.

### Playout (`app/playout/playout/`)

| Path | Behavior |
|------|----------|
| `liquidsoap/stdlib/2.0.7/*.liq` | Vendored **Liquidsoap 2.0.7 stdlib** (not present under old `libretime_playout`). Changes how built-in scripts resolve when generating Liquidsoap config. |

---

## 3. Django / DRF: `app/api/api/settings/_internal.py`

1. **`INSTALLED_APPS`**: `libretime_api.*` → `api.*`.
2. **`MIDDLEWARE`**: `api.middlewares.RequestLoggingMiddleware` added **first** (~lines 32–41).
3. **`LOGGING` / `setup_logger`**: structlog-based JSON/console handlers; logger name `api` instead of `libretime_api` (~lines 98–141).
4. **`REST_FRAMEWORK`**: `SessionAuthentication` → `SafeSessionAuthentication`, `BasicAuthentication` → `SafeBasicAuthentication` (~lines 152–166). On `UnicodeEncodeError` in auth headers, authentication returns `None` instead of crashing.
5. **`SPECTACULAR_ENUM_NAME_OVERRIDES`**: model paths updated to `api.*`.

---

## 4. API auth and permissions (`app/api/api/permissions.py`)

1. **`REQUEST_PERMISSION_TYPE_MAP`**: `POST` maps to **`"add"`** not **`"change"`** (~lines 21–30). Aligns with Django `add_*` codenames vs `permission_constants.py`.
2. **`get_own_obj`**: For `HOST`, `own_` prefix no longer derived from scanning the queryset; `GET`/`HEAD`/`OPTIONS`/`POST` → `""`; `PUT`/`PATCH`/`DELETE` → `own_` (~lines 79–96).
3. **`check_authorization_header`**: Strict **`Api-Key `** (case, single space), ASCII-only, rejects control chars, empty token, whitespace in token, `compare_digest` (~lines 113–188). **Breaking**: clients using `api-key`, `API-KEY`, or non-ASCII headers are rejected.
4. **`IsSystemTokenOrUser`**: API-Key first; anonymous without key → deny; Django `has_perm` + special cases for **`Show`**, `own_*`, host lists, `get_owner` (~lines 248–321).
5. **`IsAdminOrOwnUser`**: `has_permission` requires authenticated user + **`has_perm(perm)`** (not “superuser only”); object-level: superuser or `username` match (~lines 212–226).

---

## 5. API serializers and models (high level)

### `schedule/serializers/smart_block.py`

Replaced plain `ModelSerializer` with **`SecureModelSerializer` / `StrictSerializer`**, many `validate_*` hooks (duplicate names, formats, path-like strings in strings, etc.). Clients sending extra fields or previously accepted bad values now get **400**.

Other serializers/views with large churn (`show`, `webstream`, `playlist`, `podcasts`, `history`, `storage`, `core`) follow the same pattern: stricter validation and error responses.

### `storage/models/file.py`

Datetime columns use **`TimezoneAwareDateTimeField`**; `Meta.permissions` extended for own-file permissions.

### `urls.py`

`api_urls` is a tuple; `include(list(api_urls))` — routing behavior unchanged.

---

## 6. Analyzer (`app/analyzer/analyzer/`)

- **`message_listener.py`**: Explicit `pika` imports, typed channel/connection, restructured reconnect loop; queue name `airtime-uploads` and pipeline flow preserved; error handling differs.
- **`status_reporter.py`**, **`pipeline/pipeline.py`**, **`_ffmpeg.py`**, **`analyze_*.py`**: Reporting and pipeline error handling tightened; detailed per-line diff is large.

---

## 7. API client (`app/api-client/api_client/`)

1. **`v1.py`**: JSON via **orjson** with `OPT_SORT_KEYS` etc. — key order in bodies differs from stdlib `json` (~lines 18–27).
2. Several methods no longer accept **`**kwargs`** to `_request` (`version`, `register_component`, `notify_media_item_start_play`, …) — **breaking** for callers passing `timeout`, extra `params`, etc.

---

## 8. Playout (`app/playout/playout/`)

### `player/fetch.py`

- RabbitMQ dispatch via **`match`/`case`** and **`Commands` (str, Enum)** with same string event values (~lines 35–162).
- **`listener_timeout`** computed before `match` (interaction with `last_update_schedule_timestamp` and `POLL_INTERVAL`) — verify vs old `if/elif` timing.
- **structlog** + `logger.bind`; imports `playout.*`.

### Other playout modules

`player/liquidsoap.py`, `main.py`, `message_handler.py`, `notify/main.py`, `history/stats.py`, `*.liq` — substantial diffs for connection handling, stats, Liquidsoap templates.

### `liquidsoap/stdlib/2.0.7/`

See §2.

---

## 9. Worker (`app/worker/worker/tasks.py`)

1. Celery beat task name: `libretime_worker.tasks.*` → **`worker.tasks.legacy_trigger_task_manager`** (~lines 52–56).
2. Mutagen: **`mutagen._file.File`** instead of `mutagen.File` — **private API**, fragile across mutagen upgrades.
3. Sentry imports hoisted to module level.

---

## 10. Issues / inconsistencies

| Risk | Location | Notes |
|------|----------|--------|
| Response body in logs | `middlewares.py` ~22–25 | Possible leak of secrets/PII when `response.exception` is set. |
| `api_client` v1 | `v1.py` | Removed `**kwargs` on methods breaks extended use. |
| Mutagen | `worker/tasks.py` | Use of `mutagen._file` is brittle. |
| `IsAdminOrOwnUser` | `permissions.py` | Behavior changed from superuser-centric to Django `has_perm`. |

---

## Regeneration

Machine-readable per-file hunk list can be produced with `git diff 61813be41:<old_path> HEAD:<new_path>` over all mapped pairs (excluding tests).
