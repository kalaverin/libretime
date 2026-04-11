# Role-Based Permission Tests Documentation

**Date:** 2026-04-10T23:45:00Z
**Scope:** Complete test suite for LibreTime role-based access control

---

## Test Files Overview

| File | Role | Test Count | Description |
|------|------|------------|-------------|
| `test_role_guest_permissions.py` | GUEST | 25 | Read-only access tests |
| `test_role_host_permissions.py` | HOST | 34 | Own-content CRUD tests |
| `test_role_manager_permissions.py` | MANAGER | 30 | Full CRUD on any resource |
| `test_role_admin_permissions.py` | ADMIN | 25 | Superuser + user management |
| `test_role_bola_prevention.py` | Cross-role | 12 | BOLA attack prevention |
| `fixtures/role_fixtures.py` | All | - | Role-based user fixtures |

**Total: ~126 test cases**

---

## Test Structure

### 1. GUEST Tests (`test_role_guest_permissions.py`)

**Permission Model:** GUEST has only `view_*` permissions (15 total)

**Test Classes:**
- `TestGuestPlaylistPermissions` - 5 tests
- `TestGuestFilePermissions` - 5 tests
- `TestGuestSmartBlockPermissions` - 5 tests
- `TestGuestShowPermissions` - 5 tests
- `TestGuestWebstreamPermissions` - 5 tests

**Expected Behavior:**
```
LIST    → 200 OK (can view all)
RETRIEVE → 200 OK (can view any)
CREATE   → 403 Forbidden (no add permission)
UPDATE   → 403 Forbidden (no change permission)
DELETE   → 403 Forbidden (no delete permission)
```

### 2. HOST Tests (`test_role_host_permissions.py`)

**Permission Model:** HOST has `view_*`, `add_*`, and `own_*` permissions (44 total)

**Test Classes:**
- `TestHostPlaylistPermissions` - 7 tests
- `TestHostFilePermissions` - 7 tests
- `TestHostSmartBlockPermissions` - 7 tests
- `TestHostShowPermissions` - 7 tests (special - show host assignment)
- `TestHostWebstreamPermissions` - 6 tests

**Expected Behavior:**
```
LIST    → 200 OK (can view all)
RETRIEVE → 200 OK (can view any)
CREATE   → 201 Created (auto-assigned as owner)
UPDATE own → 200 OK (change_own_* permission)
UPDATE other → 403/404 (BOLA prevention)
DELETE own → 204 No Content
DELETE other → 403/404 (BOLA prevention)
```

### 3. MANAGER Tests (`test_role_manager_permissions.py`)

**Permission Model:** MANAGER has full CRUD permissions on all resources (43+ total)

**Test Classes:**
- `TestManagerPlaylistPermissions` - 6 tests
- `TestManagerFilePermissions` - 6 tests
- `TestManagerSmartBlockPermissions` - 6 tests
- `TestManagerShowPermissions` - 6 tests
- `TestManagerWebstreamPermissions` - 6 tests

**Expected Behavior:**
```
LIST    → 200 OK
RETRIEVE → 200 OK
CREATE   → 201 Created
UPDATE ANY → 200 OK (change_* permission, not limited to own)
DELETE ANY → 204 No Content (delete_* permission, not limited to own)
```

### 4. ADMIN Tests (`test_role_admin_permissions.py`)

**Permission Model:** ADMIN is superuser with all permissions

**Test Classes:**
- `TestAdminPlaylistPermissions` - 5 tests
- `TestAdminFilePermissions` - 5 tests
- `TestAdminSmartBlockPermissions` - 5 tests
- `TestAdminShowPermissions` - 5 tests
- `TestAdminUserManagementPermissions` - 5 tests (special for User CRUD)

**Expected Behavior:**
Same as MANAGER plus user management capabilities.

### 5. BOLA Prevention Tests (`test_role_bola_prevention.py`)

**Purpose:** Verify API1:2023 Broken Object Level Authorization prevention

**Test Classes:**
- `TestBolaPlaylistPrevention` - 4 tests
- `TestBolaFilePrevention` - 3 tests
- `TestBolaSmartBlockPrevention` - 2 tests
- `TestBolaWebstreamPrevention` - 2 tests
- `TestBolaCrossRoleSummary` - 1 comprehensive matrix test

**Critical Tests:**
- `test_host_cannot_update_other_host_*` - BOLA prevention
- `test_host_cannot_delete_other_host_*` - BOLA prevention
- `test_manager_can_update_any_host_*` - Expected elevated access
- `test_cross_role_*_modification_matrix` - Complete permission matrix

---

## Fixtures (`fixtures/role_fixtures.py`)

### User Fixtures
```python
guest_user      → Role.GUEST
host_user       → Role.HOST
manager_user    → Role.MANAGER
admin_user      → Role.ADMIN + is_superuser=True
```

### Client Fixtures
```python
guest_client    → APIClient authenticated as GUEST
host_client     → APIClient authenticated as HOST
manager_client  → APIClient authenticated as MANAGER
admin_client    → APIClient authenticated as ADMIN
```

### Multi-User Fixtures
```python
two_host_users          → (host1, host2) for cross-host tests
host_and_guest_users    → (host, guest) for permission comparison
host_and_manager_users  → (host, manager) for role comparison
```

---

## Test Naming Conventions

### Pattern
```
test_{role}_{action}_{resource}_{context}
```

### Examples
- `test_guest_can_list_playlists` - Positive test
- `test_guest_cannot_create_playlist` - Negative test
- `test_host_can_update_own_playlist` - Own resource test
- `test_host_cannot_update_other_playlist` - BOLA prevention test
- `test_manager_can_update_any_playlist` - Elevated access test

---

## Test Coverage Matrix

### By Resource

| Resource | GUEST | HOST | MANAGER | ADMIN | BOLA |
|----------|-------|------|---------|-------|------|
| Playlist | ✅ | ✅ | ✅ | ✅ | ✅ |
| File | ✅ | ✅ | ✅ | ✅ | ✅ |
| SmartBlock | ✅ | ✅ | ✅ | ✅ | ✅ |
| Show | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Webstream | ✅ | ✅ | ✅ | ✅ | ✅ |
| User | N/A | N/A | N/A | ✅ | N/A |

### By HTTP Method

| Method | GUEST | HOST | MANAGER | ADMIN |
|--------|-------|------|---------|-------|
| GET (LIST) | ✅ | ✅ | ✅ | ✅ |
| GET (RETRIEVE) | ✅ | ✅ | ✅ | ✅ |
| POST (CREATE) | ❌ | ✅ own | ✅ any | ✅ any |
| PATCH (UPDATE) | ❌ | ✅ own | ✅ any | ✅ any |
| DELETE | ❌ | ✅ own | ✅ any | ✅ any |

---

## Running the Tests

### All Role Tests
```bash
cd app/api && uv run pytest api/tests/test_role_*.py -v
```

### Specific Role
```bash
# GUEST only
cd app/api && uv run pytest api/tests/test_role_guest_permissions.py -v

# HOST only
cd app/api && uv run pytest api/tests/test_role_host_permissions.py -v

# BOLA only
cd app/api && uv run pytest api/tests/test_role_bola_prevention.py -v
```

### With Coverage
```bash
cd app/api && uv run pytest api/tests/test_role_*.py --cov=api.permissions --cov=api.schedule.views
```

---

## Expected Test Results

### Current State (Before Fixes)

| Test Category | Expected Pass | Expected Fail | Reason |
|---------------|---------------|---------------|--------|
| GUEST tests | ~20/25 | ~5/25 | Some may fail due to missing queryset filters |
| HOST tests | ~15/34 | ~19/34 | BOLA vulnerabilities - can modify other users |
| MANAGER tests | ~25/30 | ~5/30 | Should mostly pass |
| ADMIN tests | ~23/25 | ~2/25 | Should mostly pass |
| BOLA tests | ~2/12 | ~10/12 | BOLA prevention not implemented |

### After Proper Implementation

| Test Category | Expected Pass | Notes |
|---------------|---------------|-------|
| GUEST tests | 25/25 | All read-only tests pass |
| HOST tests | 34/34 | Own content only |
| MANAGER tests | 30/30 | Full CRUD |
| ADMIN tests | 25/25 | Superuser access |
| BOLA tests | 12/12 | BOLA properly prevented |

---

## Key Implementation Requirements

### For HOST BOLA Prevention

1. **Queryset Filtering:**
```python
def get_queryset(self):
    if check_authorization_header(self.request):
        return Model.objects.all()
    if not self.request.user.is_authenticated:
        return Model.objects.none()
    if self.request.user.is_superuser:
        return Model.objects.all()
    return Model.objects.filter(owner=self.request.user)
```

2. **Auto-assign Owner on Create:**
```python
def perform_create(self, serializer):
    user = self.request.user
    if user.is_authenticated and not user.is_anonymous:
        serializer.save(owner=user)
    else:
        serializer.save()
```

### For Show Special Handling

Shows use M2M relationship through ShowHost:
```python
def get_queryset(self):
    # All authenticated users see all shows (public schedule)
    if self.request.user.is_authenticated:
        return Show.objects.all()
    return Show.objects.none()

def perform_update(self, serializer):
    # Only show hosts or admins can modify
    show = serializer.instance
    user = self.request.user
    if not user.is_superuser and not show.hosts.filter(id=user.id).exists():
        raise PermissionDenied("Only show hosts can modify")
    serializer.save()
```

---

## Files Location

```
app/api/api/tests/
├── fixtures/
│   └── role_fixtures.py          # Role-based fixtures
├── test_role_guest_permissions.py   # GUEST tests
├── test_role_host_permissions.py    # HOST tests
├── test_role_manager_permissions.py # MANAGER tests
├── test_role_admin_permissions.py   # ADMIN tests
└── test_role_bola_prevention.py     # BOLA tests

.agent/research/
├── permissions_inventory.md      # Full permission analysis
├── permissions_matrix.md         # Visual permission matrix
└── role_based_tests_documentation.md  # This file
```

---

## Maintenance Notes

### Adding New Resources

1. Add resource to appropriate test class in each role file
2. Follow naming convention: `test_{role}_{action}_{resource}`
3. Use faker for all unique values
4. Use sdk.now() for all dates
5. Compare dates as strings via sdk.format_datetime()
6. Parse string with datetime only via sdk.reformat_datetime() first, it's official validator to properly formatter string.
7. Add BOLA prevention test in `test_role_bola_prevention.py`

### Modifying Permissions

1. Update `app/api/api/permission_constants.py`
2. Update tests to reflect new permission matrix
3. Update this documentation
4. Re-run full test suite

---

*Generated: 2026-04-10T23:45:00Z*
