# BOLA Investigation: T806-T809, T829-T832, T850-T854

**Date:** 2026-04-10T23:00:00Z  
**Investigator:** AI Agent  
**Scope:** API1:2023 Broken Object Level Authorization vulnerabilities

---

## Executive Summary

| Model | ViewSet | LIST | RETRIEVE | UPDATE | DELETE | Notes |
|-------|---------|------|----------|--------|--------|-------|
| **Playlist** | PlaylistViewSet | ❌ BOLA | ❌ BOLA | ❌ BOLA | ❌ BOLA | No ownership filtering |
| **SmartBlock** | SmartBlockViewSet | ❌ BOLA | ❌ BOLA | ❌ BOLA | ❌ BOLA | Kind filter only, no owner |
| **File** | FileViewSet | ❌ BOLA | ❌ BOLA | N/A | ❌ BOLA | No ownership filtering |

**Impact:** CRITICAL - Any authenticated user can access/modify/delete any other user's data.

---

## Root Cause Analysis

### Common Pattern

All three ViewSets share the same architectural flaw:

```python
# ANTI-PATTERN (current)
class VulnerableViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all()  # ← Returns ALL records
    # No get_queryset() override
```

### Missing Security Controls

1. **No ownership filtering in get_queryset()**
   - `PlaylistViewSet` - completely missing get_queryset()
   - `SmartBlockViewSet` - get_queryset() only filters by `kind`, not owner
   - `FileViewSet` - completely missing get_queryset()

2. **No ownership validation in write operations**
   - No perform_create() - owner not auto-assigned
   - No perform_update() - ownership not verified
   - No perform_destroy() - ownership not verified (FileViewSet has custom destroy but no ownership check)

3. **No anonymous access protection**
   - Unauthenticated users can list/retrieve (if IsSystemTokenOrUser allows)

---

## Detailed Findings

### T806-T809: Playlist BOLA

**File:** `app/api/api/schedule/views/playlist.py`

```python
@final
class PlaylistViewSet(viewsets.ModelViewSet[Any]):
    queryset = Playlist.objects.all()  # ← ALL playlists
    serializer_class: type[Serializer[Any]] = PlaylistSerializer
    model_permission_name: str = "playlist"
    # Missing: get_queryset(), perform_create()
```

**Attack Scenario:**
```http
# Attacker retrieves victim's playlist
GET /api/v2/playlists/123  # Victim's playlist ID
Authorization: Bearer attacker_token
# → 200 OK with victim's playlist data

# Attacker modifies victim's playlist
PATCH /api/v2/playlists/123
{"name": "Hacked Playlist"}
# → 200 OK

# Attacker deletes victim's playlist
DELETE /api/v2/playlists/123
# → 204 No Content
```

**Model Analysis:**
- Field: `owner: ForeignKey("core.User", db_column="creator_id")`
- Method: `get_owner()` returns `self.owner`

---

### T829-T832: SmartBlock BOLA

**File:** `app/api/api/schedule/views/smart_block.py`

```python
@final
class SmartBlockViewSet(viewsets.ModelViewSet[Any]):
    queryset = SmartBlock.objects.all()
    # ...
    def get_queryset(self) -> Any:
        """Filter by kind if provided."""  # ← Only kind filter, no owner
        queryset = super().get_queryset()
        kind = self.request.query_params.get("kind")
        if kind:
            queryset = queryset.filter(kind=kind)
        return queryset
```

**Attack Scenario:**
```http
# Attacker lists all smart blocks (including private)
GET /api/v2/smart-blocks
# → 200 OK with ALL users' blocks

# Attacker modifies victim's block
PATCH /api/v2/smart-blocks/456
{"kind": "dynamic"}  # Change block type
# → 200 OK
```

**Model Analysis:**
- Field: `owner: ForeignKey("core.User")`
- Method: `get_owner()` returns `self.owner`
- Already has permissions: `change_own_smartblock`, `delete_own_smartblock`

---

### T850-T854: File BOLA

**File:** `app/api/api/storage/views/file.py`

```python
@final
class FileViewSet(viewsets.ModelViewSet[Any]):
    queryset = File.objects.all()  # ← ALL files
    # Missing: get_queryset()
    # Has: perform_destroy() but no ownership check
```

**Attack Scenario:**
```http
# Attacker lists all files (metadata)
GET /api/v2/files
# → 200 OK with ALL users' files

# Attacker downloads victim's file
GET /api/v2/files/789/download
# → 200 OK with file content

# Attacker deletes victim's file
DELETE /api/v2/files/789
# → 204 No Content
```

**Model Analysis:**
- Field: `owner: ForeignKey("core.User")`
- Method: `get_owner()` returns `self.owner`
- Already has permissions: `change_own_file`, `delete_own_file`

---

## Pattern Comparison: Fixed vs Vulnerable

### Fixed Pattern (Show/Webstream)

```python
def get_queryset(self) -> Any:
    request = self.request
    # API-Key auth - full access
    if check_authorization_header(request):
        return Model.objects.all()
    # Session auth - filter by ownership
    user = request.user
    if not user.is_authenticated:
        return Model.objects.none()
    if user.is_superuser:
        return Model.objects.all()
    return Model.objects.filter(owner=user)  # ← Ownership filter

def perform_create(self, serializer):
    user = self.request.user
    if user.is_authenticated and isinstance(user, User):
        serializer.save(owner=user)  # ← Auto-assign owner
    else:
        serializer.save()
```

### Vulnerable Pattern (Playlist/SmartBlock/File)

```python
# Missing get_queryset() override OR
# get_queryset() without ownership filtering

def get_queryset(self):
    # ❌ Only filters by kind, not owner
    if kind:
        queryset = queryset.filter(kind=kind)
    return queryset

# Missing perform_create() - owner not auto-assigned
# Missing ownership check in update/destroy
```

---

## Generalization: BOLA Pattern in LibreTime

### Affected Models (Confirmed)

| Model | Module | Field | Status |
|-------|--------|-------|--------|
| Playlist | schedule | `owner` | ❌ Vulnerable |
| SmartBlock | schedule | `owner` | ❌ Vulnerable |
| File | storage | `owner` | ❌ Vulnerable |
| Show | schedule | `hosts` (M2M) | ✅ Fixed |
| Webstream | schedule | `owner` | ✅ Fixed |

### Affected Nested Resources

| Parent | Child | Access Pattern | Status |
|--------|-------|----------------|--------|
| Playlist | PlaylistContent | via `playlist` FK | ❌ Check needed |
| SmartBlock | SmartBlockContent | via `block` FK | ❌ Check needed |
| SmartBlock | SmartBlockCriteria | via `block` FK | ❌ Check needed |

---

## Recommended Fix Strategy

### Phase 1: Core Ownership Filtering

Apply the Show/Webstream pattern to all three ViewSets:

```python
def get_queryset(self):
    # Service auth: full access
    if check_authorization_header(self.request):
        return self.queryset
    # Anonymous: no access
    if not self.request.user.is_authenticated:
        return self.queryset.none()
    # Admin: full access
    if self.request.user.is_superuser:
        return self.queryset
    # User: own records only
    return self.queryset.filter(owner=self.request.user)
```

### Phase 2: Auto-assign Owner

```python
def perform_create(self, serializer):
    user = self.request.user
    if user.is_authenticated and not user.is_anonymous:
        from api.core.models import User
        if isinstance(user, User):
            serializer.save(owner=user)
            return
    serializer.save()
```

### Phase 3: Nested Resource Protection

For child resources (PlaylistContent, SmartBlockContent, SmartBlockCriteria):

```python
def get_queryset(self):
    queryset = super().get_queryset()
    # Filter by parent ownership
    if self.request.user.is_authenticated:
        queryset = queryset.filter(playlist__owner=self.request.user)
    return queryset
```

---

## Test Strategy

### Red Team Test Pattern

```python
def test_bola_retrieve_other_users_resource(self, api_client, faker):
    """Verify user cannot retrieve another user's resource."""
    # Create victim's resource
    victim = baker.make(User, username=f"victim_{faker.user_name()}")
    victim_resource = baker.make(Resource, owner=victim, ...)
    
    # Attacker tries to access
    attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
    api_client.force_authenticate(user=attacker)
    
    response = api_client.get(f"/api/v2/resources/{victim_resource.id}")
    assert response.status_code == 404  # Should not find (or 403 Forbidden)
```

---

## References

- API1:2023 Broken Object Level Authorization: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
- Fixed implementation: `app/api/api/schedule/views/show.py`
- Fixed implementation: `app/api/api/schedule/views/webstream.py`
