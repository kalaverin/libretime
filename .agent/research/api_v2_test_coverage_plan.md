# API v2 Comprehensive Test Coverage Plan

**Project:** LibreTime API v2 (app/api) - Django REST Framework
**Target:** FastAPI migration with 100% backward compatibility
**Test Framework:** pytest with model_bakery, APIClient
**Created:** 2026-04-07T18:45:00Z
**Linked Tasks:** T153-T307

---

## Overview

This document provides a detailed test coverage plan for the LibreTime API v2. The tests serve as **contract tests** — they must pass identically on both the current Django REST Framework implementation and the future FastAPI implementation.

### Testing Strategy

- **Contract-based testing:** API external interface + database behavior
- **Dual authentication:** Session (users) + Api-Key (services like liquidsoap)
- **Permission matrix:** All four roles (Guest G, Host H, Manager P, Admin A)
- **Edge cases:** Read/Write serializers, overbooked detection, cascade deletes

---

## Section 1: Infrastructure (T153-T162)

**Status:** ✅ COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| [T153](../tasks.md#t153) | Create API test infrastructure base (conftest.py) | DONE |
| [T154](../tasks.md#t154) | Create User model factory | DONE |
| [T155](../tasks.md#t155) | Create File model factory | DONE |
| [T156](../tasks.md#t156) | Create Show/Instance/Days factories | DONE |
| [T157](../tasks.md#t157) | Create Playlist/Content factories | DONE |
| [T158](../tasks.md#t158) | Create SmartBlock factories | DONE |
| [T159](../tasks.md#t159) | Create Podcast factories | DONE |
| [T160](../tasks.md#t160) | Create History model factories | DONE |
| [T161](../tasks.md#t161) | Create Schedule factory | DONE |
| [T162](../tasks.md#t162) | Create Webstream factory | DONE |

### Infrastructure Files Created

```
app/api/api/conftest.py                           # 9 auth fixtures
app/api/api/tests/fixtures/recipes.py             # 1053 lines, 25+ recipes
app/api/api/tests/fixtures/__init__.py            # 66 exports
```

### Key Fixtures Available

**Authentication:**
- `api_client` — Api-Key auth for services
- `authenticated_client` — Session auth as admin
- `host_client`, `manager_client`, `guest_client` — Role-specific clients

**Model Factories:**
- Users: `make_guest_user()`, `make_host_user()`, `make_manager_user()`, `make_admin_user()`
- Storage: `make_file()`, `make_library()`, `make_pending_file()`, `make_failed_file()`
- Shows: `make_show()`, `make_show_days()`, `make_show_instance()`, `make_modified_instance()`
- Schedule: `make_schedule()`, `make_filler_schedule()`, `make_overbooked_schedule()`
- Playlists: `make_playlist()`, `make_playlist_file()`, `make_playlist_stream()`
- SmartBlocks: `make_static_block()`, `make_dynamic_block()`, `make_genre_criteria()`
- Podcasts: `make_podcast()`, `make_podcast_episode()`
- History: `make_playout_history()`, `make_listener_count()`
- Webstreams: `make_webstream()`, `make_webstream_metadata()`

---

## Section 2: Core Module Tests (T163-T184)

**Module:** `app/api/api/core`
**Models:** User, Preference, ServiceRegister, UserToken, LoginAttempt, CeleryTask, ThirdPartyTrackReference
**Priority:** HIGH

### 2.1 Users Endpoints (T163-T172)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T163](../tasks.md#t163) | `/api/v2/users` | LIST | Response structure, pagination |
| [T164](../tasks.md#t164) | `/api/v2/users` | CREATE | User creation, MD5 password hashing |
| [T165](../tasks.md#t165) | `/api/v2/users` | CREATE | Validation errors (duplicate, invalid role) |
| [T166](../tasks.md#t166) | `/api/v2/users/{id}` | RETRIEVE | All fields, password NOT exposed |
| [T167](../tasks.md#t167) | `/api/v2/users/{id}` | RETRIEVE | 404 for non-existent |
| [T168](../tasks.md#t168) | `/api/v2/users/{id}` | UPDATE | Full PUT update |
| [T169](../tasks.md#t169) | `/api/v2/users/{id}` | PARTIAL_UPDATE | PATCH partial update |
| [T170](../tasks.md#t170) | `/api/v2/users/{id}` | DELETE | Delete user, cascade behavior |
| [T171](../tasks.md#t171) | `/api/v2/users/*` | PERMISSIONS | Admin CRUD all, user only self |
| [T172](../tasks.md#t172) | `/api/v2/users` | LIST | Filter by role (?role=H) |

**Critical Assertions:**
- Password field must NEVER appear in API responses
- MD5 hash stored (not plaintext)
- `IsAdminOrOwnUser` permission logic

### 2.2 Preferences Endpoints (T173-T175)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T173](../tasks.md#t173) | `/api/v2/preferences` | LIST | Key-value structure |
| [T174](../tasks.md#t174) | `/api/v2/preferences` | CREATE | Site and user preferences |
| [T175](../tasks.md#t175) | `/api/v2/preferences/{id}` | UPDATE | Update preference value |

### 2.3 Supporting Endpoints (T176-T181)

| Task | Endpoint | Description |
|------|----------|-------------|
| [T176](../tasks.md#t176) | `/api/v2/service-registers` | Service registration LIST |
| [T177](../tasks.md#t177) | `/api/v2/service-registers` | Heartbeat/update |
| [T178](../tasks.md#t178) | `/api/v2/user-tokens` | Token CRUD (password reset) |
| [T179](../tasks.md#t179) | `/api/v2/login-attempts` | Login attempt tracking |
| [T180](../tasks.md#t180) | `/api/v2/celery-tasks` | Background task LIST |
| [T181](../tasks.md#t181) | `/api/v2/third-party-track-references` | External track CRUD |

### 2.4 Public Endpoints (T182-T183)

| Task | Endpoint | Auth | Test Focus |
|------|----------|------|------------|
| [T182](../tasks.md#t182) | `/api/v2/info` | AllowAny | station_name in response |
| [T183](../tasks.md#t183) | `/api/v2/version` | AllowAny | api_version format |

### 2.5 Stream Endpoints (T184-T185)

| Task | Endpoint | Type | Description |
|------|----------|------|-------------|
| [T184](../tasks.md#t184) | `/api/v2/stream/preferences` | Computed | All stream settings |
| [T185](../tasks.md#t185) | `/api/v2/stream/state` | Computed | Boolean flags |

---

## Section 3: Storage Module Tests (T186-T200)

**Module:** `app/api/api/storage`
**Models:** File, Library
**Priority:** CRITICAL — Files are largest model, download action critical

### 3.1 Files Endpoints (T186-T196)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T186](../tasks.md#t186) | `/api/v2/files` | LIST | All 50+ fields, proper typing |
| [T187](../tasks.md#t187) | `/api/v2/files` | LIST | Filters: ?md5=, ?genre=, combined |
| [T188](../tasks.md#t188) | `/api/v2/files` | CREATE | All metadata fields, ImportStatus |
| [T189](../tasks.md#t189) | `/api/v2/files/{id}` | RETRIEVE | Metadata, computed fields |
| [T190](../tasks.md#t190) | `/api/v2/files/{id}` | UPDATE | Update metadata (artist, title) |
| [T191](../tasks.md#t191) | `/api/v2/files/{id}` | DELETE | Remove from filesystem + DB |
| [T192](../tasks.md#t192) | `/api/v2/files/{id}` | DELETE | 404 for non-existent |
| [T195](../tasks.md#t195) | `/api/v2/files/*` | PERMISSIONS | Owner edit, admin all, other read-only |
| [T196](../tasks.md#t196) | `/api/v2/files` | CREATE | Validation (invalid mime, size) |

### 3.2 Files Custom Action — CRITICAL (T193-T194)

| Task | Endpoint | Custom Action | Test Focus |
|------|----------|---------------|------------|
| [T193](../tasks.md#t193) | `/api/v2/files/{id}/download` | GET | X-Accel-Redirect header for nginx |
| [T194](../tasks.md#t194) | `/api/v2/files/{id}/download` | GET | 404 for non-existent file |

**Critical:** Download action uses `X-Accel-Redirect` header for nginx file serving. This must work identically in FastAPI.

### 3.3 Libraries Endpoints (T197-T200)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T197](../tasks.md#t197) | `/api/v2/libraries` | LIST | Track types |
| [T198](../tasks.md#t198) | `/api/v2/libraries` | CREATE | Code, name, description |
| [T199](../tasks.md#t199) | `/api/v2/libraries/{id}` | UPDATE | Description, enabled flag |
| [T200](../tasks.md#t200) | `/api/v2/libraries/{id}` | DELETE | Cascade with files |

---

## Section 4: Schedule Module Tests (T201-T258)

**Module:** `app/api/api/schedule`
**Models:** Show, ShowDays, ShowInstance, ShowRebroadcast, ShowHost, Playlist, PlaylistContent, SmartBlock, SmartBlockContent, SmartBlockCriteria, Schedule, Webstream, WebstreamMetadata
**Priority:** CRITICAL — Most complex module, Read/Write serializers

### 4.1 Shows Endpoints (T201-T209)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T201](../tasks.md#t201) | `/api/v2/shows` | LIST | All fields, hosts relationship |
| [T202](../tasks.md#t202) | `/api/v2/shows` | CREATE | With hosts assigned |
| [T203](../tasks.md#t203) | `/api/v2/shows` | CREATE | With live_stream_user/pass |
| [T204](../tasks.md#t204) | `/api/v2/shows` | CREATE | With autoplaylist_id |
| [T205](../tasks.md#t205) | `/api/v2/shows/{id}` | RETRIEVE | Computed: live_enabled |
| [T206](../tasks.md#t206) | `/api/v2/shows/{id}` | UPDATE | Metadata (name, desc, colors) |
| [T207](../tasks.md#t207) | `/api/v2/shows/{id}` | UPDATE | Add/remove hosts |
| [T208](../tasks.md#t208) | `/api/v2/shows/{id}` | DELETE | Cascade to instances, days |
| [T209](../tasks.md#t209) | `/api/v2/shows/*` | PERMISSIONS | Host can edit own show |

**Computed Fields:**
- `live_enabled = live_auth_registered OR live_auth_custom`

### 4.2 ShowDays Endpoints (T210-T214)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T210](../tasks.md#t210) | `/api/v2/show-days` | LIST | Repeat patterns |
| [T211](../tasks.md#t211) | `/api/v2/show-days` | CREATE | Weekly repeat (RepeatKind.WEEKLY=0) |
| [T212](../tasks.md#t212) | `/api/v2/show-days` | CREATE | Monthly repeat (RepeatKind.MONTHLY=2) |
| [T213](../tasks.md#t213) | `/api/v2/show-days/{id}` | UPDATE | Change pattern, time |
| [T214](../tasks.md#t214) | `/api/v2/show-days/{id}` | DELETE | Instance generation affected |

**Repeat Kinds:**
- WEEKLY = 0
- WEEKLY_2 = 1 (bi-weekly)
- WEEKLY_3 = 4
- WEEKLY_4 = 5
- MONTHLY = 2

### 4.3 ShowInstances Endpoints (T215-T218)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T215](../tasks.md#t215) | `/api/v2/show-instances` | LIST | For a show |
| [T216](../tasks.md#t216) | `/api/v2/show-instances/{id}` | RETRIEVE | starts/ends, filled_time |
| [T217](../tasks.md#t217) | `/api/v2/show-instances/{id}` | UPDATE | Mark modified, change desc |
| [T218](../tasks.md#t218) | `/api/v2/show-instances/{id}` | DELETE | Single vs all following |

### 4.4 ShowRebroadcasts & ShowHosts (T219-T222)

| Task | Endpoint | Description |
|------|----------|-------------|
| [T219](../tasks.md#t219) | `/api/v2/show-rebroadcasts` | Rebroadcast schedules CRUD |
| [T220](../tasks.md#t220) | `/api/v2/show-hosts` | LIST hosts for show |
| [T221](../tasks.md#t221) | `/api/v2/show-hosts` | CREATE add host |
| [T222](../tasks.md#t222) | `/api/v2/show-hosts/{id}` | DELETE remove host |

### 4.5 Playlists Endpoints (T223-T227)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T223](../tasks.md#t223) | `/api/v2/playlists` | LIST | Computed: length |
| [T224](../tasks.md#t224) | `/api/v2/playlists` | CREATE | With owner |
| [T225](../tasks.md#t225) | `/api/v2/playlists/{id}` | UPDATE | Name/description |
| [T226](../tasks.md#t226) | `/api/v2/playlists/{id}` | DELETE | Cascade to contents |
| [T227](../tasks.md#t227) | `/api/v2/playlists/*` | PERMISSIONS | Owner edit, other read |

### 4.6 PlaylistContents Endpoints (T228-T233)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T228](../tasks.md#t228) | `/api/v2/playlist-contents` | LIST | Order by position |
| [T229](../tasks.md#t229) | `/api/v2/playlist-contents` | CREATE | Add file (Kind.FILE=0) |
| [T230](../tasks.md#t230) | `/api/v2/playlist-contents` | CREATE | Add stream (Kind.STREAM=1) |
| [T231](../tasks.md#t231) | `/api/v2/playlist-contents` | CREATE | Add block (Kind.BLOCK=2) |
| [T232](../tasks.md#t232) | `/api/v2/playlist-contents/{id}` | UPDATE | Reorder (position) |
| [T233](../tasks.md#t233) | `/api/v2/playlist-contents/{id}` | DELETE | Remove item |

### 4.7 SmartBlocks Endpoints (T234-T238)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T234](../tasks.md#t234) | `/api/v2/smart-blocks` | LIST | Static vs dynamic (kind) |
| [T235](../tasks.md#t235) | `/api/v2/smart-blocks` | CREATE | Static block |
| [T236](../tasks.md#t236) | `/api/v2/smart-blocks` | CREATE | Dynamic block |
| [T237](../tasks.md#t237) | `/api/v2/smart-blocks/{id}` | UPDATE | Metadata |
| [T238](../tasks.md#t238) | `/api/v2/smart-blocks/{id}` | DELETE | Cascade to contents/criteria |

**Kinds:** STATIC = "static", DYNAMIC = "dynamic"

### 4.8 SmartBlockContents & Criteria (T239-T244)

| Task | Endpoint | Method | Description |
|------|----------|--------|-------------|
| [T239](../tasks.md#t239) | `/api/v2/smart-block-contents` | LIST | Static block contents |
| [T240](../tasks.md#t240) | `/api/v2/smart-block-contents` | CREATE | Add file to static block |
| [T241](../tasks.md#t241) | `/api/v2/smart-block-criteria` | LIST | Dynamic block criteria |
| [T242](../tasks.md#t242) | `/api/v2/smart-block-criteria` | CREATE | Genre=Jazz, etc. |
| [T243](../tasks.md#t243) | `/api/v2/smart-block-criteria/{id}` | UPDATE | Modify condition/value |
| [T244](../tasks.md#t244) | `/api/v2/smart-block-criteria/{id}` | DELETE | Remove criteria |

### 4.9 Webstreams Endpoints (T245-T249)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T245](../tasks.md#t245) | `/api/v2/webstreams` | LIST | External streams |
| [T246](../tasks.md#t246) | `/api/v2/webstreams` | CREATE | With URL validation |
| [T247](../tasks.md#t247) | `/api/v2/webstreams/{id}` | UPDATE | Edit URL |
| [T248](../tasks.md#t248) | `/api/v2/webstreams/{id}` | DELETE | Remove stream |
| [T249](../tasks.md#t249) | `/api/v2/webstream-metadata` | LIST | Liquidsoap data |

### 4.10 Schedule Endpoints — CRITICAL (T250-T258)

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T250](../tasks.md#t250) | `/api/v2/schedule` | LIST | Filters: starts_after, starts_before |
| [T251](../tasks.md#t251) | `/api/v2/schedule` | LIST | ?overbooked=true/false |
| [T252](../tasks.md#t252) | `/api/v2/schedule` | CREATE | Schedule file |
| [T253](../tasks.md#t253) | `/api/v2/schedule` | CREATE | Schedule stream |
| [T254](../tasks.md#t254) | `/api/v2/schedule/{id}` | RETRIEVE | Computed: cue_out_calculated |
| [T255](../tasks.md#t255) | `/api/v2/schedule/{id}` | RETRIEVE | Computed: ends_at_calculated |
| [T256](../tasks.md#t256) | `/api/v2/schedule/{id}` | UPDATE | Reschedule (change time) |
| [T257](../tasks.md#t257) | `/api/v2/schedule/{id}` | DELETE | Unschedule |
| [T258](../tasks.md#t258) | `/api/v2/schedule/*` | PERMISSIONS | Show host can modify |

**CRITICAL — ReadWriteSerializerMixin:**
- **GET** uses `ScheduleReadSerializer` — excludes `cue_out`, computes `cue_out_calculated`
- **POST/PUT/PATCH** uses `ScheduleWriteSerializer` — includes `cue_out` for setting
- FastAPI must replicate this dual-serializer behavior

---

## Section 5: History Module Tests (T259-T267)

**Module:** `app/api/api/history`
**Models:** PlayoutHistory, PlayoutHistoryTemplate, ListenerCount, LiveLog, MountName
**Priority:** HIGH

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T259](../tasks.md#t259) | `/api/v2/playout-history` | LIST | Filters: instance_id, time range |
| [T260](../tasks.md#t260) | `/api/v2/playout-history` | CREATE | Record played item |
| [T261](../tasks.md#t261) | `/api/v2/playout-history/{id}` | RETRIEVE | Entry details |
| [T262](../tasks.md#t262) | `/api/v2/playout-history-templates` | LIST | Templates |
| [T263](../tasks.md#t263) | `/api/v2/playout-history-templates` | CREATE | Create template |
| [T264](../tasks.md#t264) | `/api/v2/listener-counts` | LIST | Timestamp ordering |
| [T265](../tasks.md#t265) | `/api/v2/live-logs` | LIST | Filters: time, show |
| [T266](../tasks.md#t266) | `/api/v2/live-logs` | CREATE | Record live event |
| [T267](../tasks.md#t267) | `/api/v2/mount-names` | LIST | Icecast mount points |

---

## Section 6: Podcasts Module Tests (T268-T278)

**Module:** `app/api/api/podcasts`
**Models:** Podcast, PodcastEpisode, StationPodcast, ImportedPodcast
**Priority:** HIGH

| Task | Endpoint | Method | Test Focus |
|------|----------|--------|------------|
| [T268](../tasks.md#t268) | `/api/v2/podcasts` | LIST | iTunes metadata |
| [T269](../tasks.md#t269) | `/api/v2/podcasts` | CREATE | With RSS URL |
| [T270](../tasks.md#t270) | `/api/v2/podcasts/{id}` | UPDATE | Metadata |
| [T271](../tasks.md#t271) | `/api/v2/podcasts/{id}` | DELETE | Remove podcast |
| [T272](../tasks.md#t272) | `/api/v2/podcasts/{id}/sync` | ACTION | Fetch latest episodes |
| [T273](../tasks.md#t273) | `/api/v2/podcast-episodes` | LIST | Episodes for podcast |
| [T274](../tasks.md#t274) | `/api/v2/podcast-episodes` | CREATE | Add episode manually |
| [T275](../tasks.md#t275) | `/api/v2/podcast-episodes/{id}` | UPDATE | Edit episode |
| [T276](../tasks.md#t276) | `/api/v2/podcast-episodes/{id}` | DELETE | Remove episode |
| [T277](../tasks.md#t277) | `/api/v2/station-podcast` | LIST/GET | Station's own feed |
| [T278](../tasks.md#t278) | `/api/v2/imported-podcasts` | LIST/GET | Auto-imported episodes |

---

## Section 7: Authentication Tests (T279-T283)

**Priority:** CRITICAL

| Task | Test | Description |
|------|------|-------------|
| [T279](../tasks.md#t279) | Session auth | Logged-in user access |
| [T280](../tasks.md#t280) | Api-Key auth | Service token (liquidsoap) |
| [T281](../tasks.md#t281) | No auth 403 | Unauthenticated rejection |
| [T282](../tasks.md#t282) | Invalid Api-Key 403 | Bad token rejection |
| [T283](../tasks.md#t283) | Public endpoints | info, version no auth |

**Permission Classes:**
- `IsSystemTokenOrUser` — Allows Api-Key OR session
- `IsAdminOrOwnUser` — Admin or owner only
- `AllowAny` — Public endpoints

---

## Section 8: Edge Cases & Integration (T284-T298)

**Priority:** CRITICAL for FastAPI migration

| Task | Test | Description |
|------|------|-------------|
| [T284](../tasks.md#t284) | ReadWriteSerializerMixin | Schedule GET vs POST different schemas |
| [T285](../tasks.md#t285) | Overbooked detection | Item beyond show instance |
| [T286](../tasks.md#t286) | Instance generation | Show days → instances |
| [T287](../tasks.md#t287) | Playlist length calc | Computed from contents |
| [T288](../tasks.md#t288) | Dynamic block query | Criteria → SQL generation |
| [T289](../tasks.md#t289) | Unique constraint | filepath + md5 |
| [T290](../tasks.md#t290) | Cascade deletes | Show→instances, playlist→contents |
| [T291](../tasks.md#t291) | Pagination | ?page=, ?limit= |
| [T292](../tasks.md#t292) | Concurrent edits | Transaction isolation |
| [T293](../tasks.md#t293) | Large payloads | 1000+ items performance |
| [T294](../tasks.md#t294) | Metadata extraction | Upload triggers analyzer |
| [T295](../tasks.md#t295) | ReplayGain calc | Audio analysis |
| [T296](../tasks.md#t296) | API versioning | /api/v2/ prefix |
| [T297](../tasks.md#t297) | CORS headers | Browser clients |
| [T298](../tasks.md#t298) | Rate limiting | Auth endpoints |

---

## Section 9: Documentation (T299-T307)

| Task | Document | Description |
|------|----------|-------------|
| [T299](../tasks.md#t299) | Fixtures README | All fixtures documented |
| [T300](../tasks.md#t300) | Test run guide | `cd app/api && uv run pytest` |
| [T301](../tasks.md#t301) | Contract test guide | FastAPI migration philosophy |
| [T302](../tasks.md#t302) | Baseline verification | Existing tests still pass |
| [T303](../tasks.md#t303) | Coverage reporting | pytest-cov setup |
| [T304](../tasks.md#t304) | Troubleshooting | Common issues guide |
| [T305](../tasks.md#t305) | Mock utilities | External service mocks |
| [T306](../tasks.md#t306) | Parameterized tests | @pytest.mark.parametrize examples |
| [T307](../tasks.md#t307) | Performance benchmarks | Timing assertions |

---

## Critical Path for FastAPI Migration

These tests MUST be implemented first — they validate core functionality that liquidsoap and the web UI depend on:

1. **T153-T162** — Infrastructure ✅ DONE
2. **T163-T168, T173-T184** — Core endpoints
3. **T186-T194** — Files (especially T193 download action)
4. **T201-T258** — Schedule (complex relationships)
5. **T279-T283** — Authentication
6. **T284** — ReadWriteSerializerMixin behavior

---

## Test File Organization (Proposed)

```
app/api/api/tests/
├── conftest.py                      # Already exists, extended
├── fixtures/                        # ✅ DONE
│   ├── __init__.py
│   └── recipes.py
├── test_permissions.py              # Existing
├── core/                            # T163-T184
│   ├── test_users.py
│   ├── test_preferences.py
│   ├── test_stream.py
│   └── test_public.py
├── storage/                         # T186-T200
│   └── test_files.py
├── schedule/                        # T201-T258
│   ├── test_shows.py
│   ├── test_show_instances.py
│   ├── test_playlists.py
│   ├── test_smart_blocks.py
│   ├── test_schedule.py
│   └── test_webstreams.py
├── history/                         # T259-T267
│   └── test_history.py
└── podcasts/                        # T268-T278
    └── test_podcasts.py
```

---

## Estimated Implementation

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| Infrastructure | T153-T162 | ✅ 2.5 hours |
| Core module | T163-T184 | 2-3 days |
| Storage module | T186-T200 | 1-2 days |
| Schedule module | T201-T258 | 3-4 days |
| History module | T259-T267 | 1 day |
| Podcasts module | T268-T278 | 1-2 days |
| Auth & Edge cases | T279-T298 | 2 days |
| Documentation | T299-T307 | 1 day |
| **TOTAL** | **155 tasks** | **2-3 weeks** |

---

## Notes

- **Line length:** 79 characters (project standard)
- **Type hints:** Required (Python 3.10+)
- **Import order:** future → stdlib → third-party → first-party → local
- **Test runner:** `cd app/api && uv run pytest`
- **Coverage:** `pytest --cov=api --cov-report=html`

---

*This plan is linked to .agent/tasks.md tasks T153-T307.*

---

## Appendix: Test Environment Setup

### Docker Compose Test Environment

**File:** `docker-compose.test.yml` (isolated, ephemeral)

**Services:**
| Service | Port | Credentials | Purpose |
|---------|------|-------------|---------|
| PostgreSQL | 5432 | libretime/libretime | Test database |
| RabbitMQ | 5672 | libretime/libretime | Message queue |
| Redis | 6379 | - | Cache/sessions (future) |

**Start environment:**
```bash
docker compose -f docker-compose.test.yml up -d
```

**Check status:**
```bash
docker compose -f docker-compose.test.yml ps
```

**Stop environment:**
```bash
docker compose -f docker-compose.test.yml down
```

**Full test cycle:**
```bash
# 1. Start services
docker compose -f docker-compose.test.yml up -d

# 2. Wait for services (5-10 sec)
sleep 5

# 3. Run tests
cd app/api
uv run pytest api/core/tests/models/ -v
uv run pytest api/tests/test_permissions.py -v

# 4. Stop services
docker compose -f docker-compose.test.yml down
```

**Environment Variables (auto-configured):**
- `POSTGRES_DB=libretime_test`
- `POSTGRES_USER=libretime`
- `POSTGRES_PASSWORD=libretime`
- `POSTGRES_HOST=localhost`
- `POSTGRES_PORT=5432`

**Database Setup:**
Test runner automatically applies migrations. No manual setup needed.
