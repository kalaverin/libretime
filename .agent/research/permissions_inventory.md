# LibreTime Permissions Inventory

**Date:** 2026-04-10T23:30:00Z  
**Investigator:** AI Agent  
**Scope:** Complete analysis of Django permissions, DRF permission classes, and role-based access control

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERMISSION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Request → Authentication → IsSystemTokenOrUser → has_perm() → Database    │
│                            (DRF Permission)      (User model)               │
│                                     │                                       │
│                                     ↓                                       │
│                            get_permission_for_view()                        │
│                            (HTTP method → permission type)                  │
│                                     │                                       │
│                                     ↓                                       │
│                            get_own_obj() → "own_" prefix?                   │
│                            (Check if HOST + single owner)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Permission Classes (DRF)

### 2.1 IsSystemTokenOrUser

**Location:** `app/api/api/permissions.py:106`

**Purpose:** Main permission class for all ModelViewSets except User

**Logic:**
| Auth Type | Permission Check |
|-----------|-----------------|
| API-Key (service) | ✅ Always allowed |
| Session + Authenticated | Check Django permissions via `has_perm(perm, obj)` |
| Anonymous | ❌ Denied |

**Usage in ViewSets:**
- Default (via settings): `DEFAULT_PERMISSION_CLASSES`
- Explicit in: StreamPreferencesViewSet

### 2.2 IsAdminOrOwnUser

**Location:** `app/api/api/permissions.py:79`

**Purpose:** Special permission for User management

**Logic:**
| User Type | List/Create | Retrieve/Update/Delete |
|-----------|-------------|------------------------|
| Superuser | ✅ All | ✅ All |
| Authenticated | ❌ None | ✅ Only self (username match) |
| Anonymous | ❌ None | ❌ None |

**Usage:**
- UserViewSet only

**Bug:** Crashes on AnonymousUser (T308)

---

## 3. Role-Based Permission System

### 3.1 Roles

| Role | Code | Description |
|------|------|-------------|
| GUEST | "G" | Read-only viewer |
| HOST | "H" | Creates own content, modifies own |
| MANAGER | "P" | Full access to all content |
| ADMIN | "A" | Superuser - system admin |

### 3.2 Permission Constants by Role

#### GUEST_PERMISSIONS (`app/api/api/permission_constants.py`)

```python
"view_schedule"
"view_show"
"view_showdays"
"view_showhost"
"view_showinstance"
"view_showrebroadcast"
"view_file"
"view_podcast"
"view_podcastepisode"
"view_playlist"
"view_playlistcontent"
"view_smartblock"
"view_smartblockcontent"
"view_smartblockcriteria"
"view_webstream"
"view_apiroot"
```

**Total: 15 permissions (VIEW only)**

#### HOST_PERMISSIONS

**Extends GUEST + CREATE + OWN modifications:**

```python
# CREATE permissions
"add_file"
"add_podcast"
"add_podcastepisode"
"add_playlist"
"add_playlistcontent"
"add_smartblock"
"add_smartblockcontent"
"add_smartblockcriteria"
"add_webstream"

# OWN modifications (custom model permissions)
"change_own_schedule"
"delete_own_schedule"
"change_own_file"
"delete_own_file"
"change_own_podcast"
"delete_own_podcast"
"change_own_podcastepisode"
"delete_own_podcastepisode"
"change_own_playlist"
"delete_own_playlist"
"change_own_playlistcontent"
"delete_own_playlistcontent"
"change_own_smartblock"
"delete_own_smartblock"
"change_own_smartblockcontent"
"delete_own_smartblockcontent"
"change_own_smartblockcriteria"
"delete_own_smartblockcriteria"
"change_own_webstream"
"delete_own_webstream"
```

**Total: 9 add + 20 own_* = 29 permissions**

#### MANAGER_PERMISSIONS

**Extends GUEST + ALL modifications:**

```python
# Show management
"add_show"
"add_showdays"
"add_showhost"
"add_showinstance"
"add_showrebroadcast"

# Full file control
"add_file"
"change_file"
"delete_file"

# Full podcast control
"add_podcast"
"change_podcast"
"delete_podcast"
"add_podcastepisode"
"change_podcastepisode"
"delete_podcastepisode"

# Full playlist control
"add_playlist"
"change_playlist"
"delete_playlist"
"add_playlistcontent"
"change_playlistcontent"
"delete_playlistcontent"

# Full smartblock control
"add_smartblock"
"change_smartblock"
"delete_smartblock"
"add_smartblockcontent"
"change_smartblockcontent"
"delete_smartblockcontent"
"add_smartblockcriteria"
"change_smartblockcriteria"
"delete_smartblockcriteria"

# Full webstream control
"add_webstream"
"change_webstream"
"delete_webstream"

# Full schedule control
"change_schedule"
"delete_schedule"

# Show control
"change_show"
"delete_show"
"change_showdays"
"delete_showdays"
"change_showhost"
"delete_showhost"
"change_showinstance"
"delete_showinstance"
"change_showrebroadcast"
"delete_showrebroadcast"
```

**Total: 43 permissions (full CRUD)**

---

## 4. Model Permissions (Django)

### 4.1 Custom Model Permissions (defined in Meta)

| Model | Custom Permissions |
|-------|-------------------|
| **Schedule** | `change_own_schedule`, `delete_own_schedule` |
| **File** | `change_own_file`, `delete_own_file` |
| **Webstream** | `change_own_webstream`, `delete_own_webstream` |
| **SmartBlock** | `change_own_smartblock` |
| **SmartBlockContent** | `change_own_smartblockcontent` |
| **SmartBlockCriteria** | `change_own_smartblockcriteria` |

**Podcast models** (in `app/api/api/podcasts/models/podcast.py`):
- Podcast: custom permissions exist
- PodcastEpisode: custom permissions exist

### 4.2 Default Django Permissions

For each model without explicit `default_permissions = []`, Django auto-creates:
- `add_<model>`
- `change_<model>`
- `delete_<model>`
- `view_<model>`

---

## 5. ViewSet Permission Matrix

### 5.1 Full Matrix

| ViewSet | permission_classes | model_permission_name | Notes |
|---------|-------------------|----------------------|-------|
| **core/views/info.py** | | | |
| InfoViewSet | `(AllowAny,)` | - | Public endpoint |
| VersionViewSet | `(AllowAny,)` | - | Public endpoint |
| **core/views/user.py** | | | |
| UserViewSet | `(IsAdminOrOwnUser,)` | `"user"` | Special permission |
| **core/views/preference.py** | | | |
| PreferenceViewSet | Default (IsSystemTokenOrUser) | `"preference"` | |
| **core/views/service.py** | | | |
| ServiceRegisterViewSet | Default | `"serviceregister"` | |
| **core/views/worker.py** | | | |
| ThirdPartyTrackReferenceViewSet | Default | `"thirdpartytrackreference"` | |
| CeleryTaskViewSet | Default | `"celerytask"` | |
| **core/views/auth.py** | | | |
| UserTokenViewSet | Default | `"usertoken"` | |
| LoginAttemptViewSet | Default | `"loginattempt"` | |
| **core/views/stream.py** | | | |
| StreamSettingViewSet | `(IsSystemTokenOrUser,)` | `"streamsetting"` | Explicit permission class |
| **schedule/views/show.py** | | | |
| ShowViewSet | Default | `"show"` | |
| ShowDaysViewSet | Default | `"showdays"` | |
| ShowHostViewSet | Default | `"showhost"` | |
| ShowInstanceViewSet | Default | `"showinstance"` | |
| ShowRebroadcastViewSet | Default | `"showrebroadcast"` | |
| **schedule/views/playlist.py** | | | |
| PlaylistViewSet | Default | `"playlist"` | **MISSING ownership filter** |
| PlaylistContentViewSet | Default | `"playlistcontent"` | |
| **schedule/views/smart_block.py** | | | |
| SmartBlockViewSet | Default | `"smartblock"` | **MISSING ownership filter** |
| SmartBlockContentViewSet | Default | `"smartblockcontent"` | |
| SmartBlockCriteriaViewSet | Default | `"smartblockcriteria"` | |
| **schedule/views/schedule.py** | | | |
| ScheduleViewSet | Default | `"schedule"` | |
| **schedule/views/webstream.py** | | | |
| WebstreamViewSet | Default | `"webstream"` | ✅ Fixed with ownership filter |
| WebstreamMetadataViewSet | Default | `"webstreammetadata"` | |
| **storage/views/file.py** | | | |
| FileViewSet | Default | `"file"` | **MISSING ownership filter** |
| **storage/views/library.py** | | | |
| LibraryViewSet | Default | `"library"` | |
| **podcasts/views/podcast.py** | | | |
| PodcastViewSet | Default | `"podcast"` | |
| PodcastEpisodeViewSet | Default | `"podcastepisode"` | |
| StationPodcastViewSet | Default | `"station"` | |
| ImportedPodcastViewSet | Default | `"importedpodcast"` | |
| **history/views/played.py** | | | |
| PlayoutHistoryViewSet | Default | `"playouthistory"` | |
| PlayoutHistoryMetadataViewSet | Default | `"playouthistorymetadata"` | |
| PlayoutHistoryTemplateViewSet | Default | `"playouthistorytemplate"` | |
| PlayoutHistoryTemplateFieldViewSet | Default | `"playouthistorytemplatefield"` | |
| **history/views/listener.py** | | | |
| MountNameViewSet | Default | `"mountname"` | |
| TimestampViewSet | Default | `"timestamp"` | |
| ListenerCountViewSet | Default | `"listenercount"` | |
| **history/views/live.py** | | | |
| LiveLogViewSet | Default | `"livelog"` | |

---

## 6. Permission Translation Flow

### 6.1 HTTP Method to Permission Type

```python
REQUEST_PERMISSION_TYPE_MAP = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "change",
    "PUT": "change",
    "DELETE": "delete",
    "PATCH": "change",
}
```

### 6.2 Full Permission Name Construction

```
{action}_{own_prefix}{model_name}

Where:
- action: view | change | delete | add
- own_prefix: "own_" | "" (depends on get_own_obj())
- model_name: from view.model_permission_name
```

### 6.3 get_own_obj() Logic

```python
def get_own_obj(request, view):
    user = request.user
    
    # Not a HOST role → no "own_" prefix
    if user is None or user.role != Role.HOST or request.method == "GET":
        return ""
    
    # Check if queryset has single owner
    qs = view.queryset.all()  # ← BUG: should check specific object
    for model in qs:
        owner = model.get_owner()
        if owner not in model_owners:
            model_owners.append(owner)
    
    # If single owner and it's current user → "own_"
    if len(model_owners) == 1 and user in model_owners:
        return "own_"
    
    return ""
```

**CRITICAL BUG:** Checks `view.queryset.all()` (ALL records in table) instead of specific object!

---

## 7. Security Analysis

### 7.1 BOLA Vulnerabilities (API1:2023)

| Resource | Issue | Status |
|----------|-------|--------|
| Playlist | No ownership filtering in get_queryset() | ❌ Vulnerable |
| SmartBlock | No ownership filtering in get_queryset() | ❌ Vulnerable |
| File | No ownership filtering in get_queryset() | ❌ Vulnerable |
| Show | Returns all shows (may be intentional) | ⚠️ Design decision |
| Webstream | ✅ Fixed with ownership filter | ✅ Secure |

### 7.2 Permission Bypass Vectors

| Vector | Description | Risk |
|--------|-------------|------|
| API-Key auth | Services bypass all permission checks | High - service compromise |
| get_own_obj() bug | Checks entire table, not specific object | High - BOLA |
| Missing queryset filter | ViewSets return all records | Critical - data leak |
| IsAdminOrOwnUser crash | AnonymousUser crashes permission check | Medium - DoS |

### 7.3 Permission Matrix by Role

#### GUEST (Read-Only)

| Resource | LIST | RETRIEVE | CREATE | UPDATE | DELETE |
|----------|------|----------|--------|--------|--------|
| Show | ✅ | ✅ | ❌ | ❌ | ❌ |
| Playlist | ✅ | ✅ | ❌ | ❌ | ❌ |
| File | ✅ | ✅ | ❌ | ❌ | ❌ |
| SmartBlock | ✅ | ✅ | ❌ | ❌ | ❌ |
| Schedule | ✅ | ✅ | ❌ | ❌ | ❌ |

**Issue:** GUEST can see ALL playlists/files from ALL users due to missing queryset filters.

#### HOST (Own Content)

| Resource | LIST | RETRIEVE | CREATE | UPDATE | DELETE |
|----------|------|----------|--------|--------|--------|
| Show | ✅ | ✅ | ? | own shows | ? |
| Playlist | ✅ | ✅ | ✅ | own | own |
| File | ✅ | ✅ | ✅ | own | own |
| SmartBlock | ✅ | ✅ | ✅ | own | own |

**Issue:** LIST shows ALL records, filtering should be in get_queryset().

#### MANAGER (Full Access)

| Resource | LIST | RETRIEVE | CREATE | UPDATE | DELETE |
|----------|------|----------|--------|--------|--------|
| All | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 8. Recommendations

### 8.1 Immediate Fixes Required

1. **Add ownership filtering to all ViewSets:**
   ```python
   def get_queryset(self):
       if check_authorization_header(self.request):
           return Model.objects.all()
       if not self.request.user.is_authenticated:
           return Model.objects.none()
       if self.request.user.is_superuser():
           return Model.objects.all()
       return Model.objects.filter(owner=self.request.user)
   ```

2. **Fix get_own_obj() bug:**
   - Should check specific object, not entire table
   - Should work with object-level permissions

3. **Add perform_create() for auto-assigning owner:**
   ```python
   def perform_create(self, serializer):
       serializer.save(owner=self.request.user)
   ```

### 8.2 Design Improvements

1. **Explicit permission classes per ViewSet:**
   - Don't rely on global default
   - Make permissions explicit and documented

2. **Separate read/write queryset logic:**
   - Different filtering for LIST/RETRIEVE vs UPDATE/DELETE

3. **Audit permission constants:**
   - Verify all required permissions exist
   - Add missing `*_own_*` permissions for all owned models

---

## 9. References

- `app/api/api/permissions.py` - DRF permission classes
- `app/api/api/permission_constants.py` - Role-based permissions
- `app/api/api/core/models/user.py` - User.has_perm() implementation
- `app/api/api/core/models/role.py` - Role definitions
- OWASP API1:2023 - Broken Object Level Authorization
