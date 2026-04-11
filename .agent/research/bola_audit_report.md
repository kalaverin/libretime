# BOLA Audit Report - Test Reproducibility Analysis

**Date:** 2026-04-11T04:30:00Z  
**Scope:** Tasks from issues.md vs actual implementation state  
**Test Results:** 43 failed, 343 passed in test_role_*.py

---

## Executive Summary

Критическая проблема: Фильтрация в `get_queryset()` сломала VIEW операции для GUEST и HOST ролей.

Согласно ролевой модели LibreTime:
- **GUEST**: Видит ВСЁ (read-only viewer)
- **HOST**: Видит ВСЁ + создаёт/изменяет только свои
- **MANAGER/ADMIN**: Полный доступ

Но текущая реализация с `get_queryset()` фильтрацией возвращает 404 для чужих объектов при RETRIEVE.

---

## Type A: Tasks That REPEAT (Even With Correct Implementation)

Эти задачи описывают BOLA уязвимости, но при правильной реализации **не являются багами**:

### VIEW Operations (By Design - Not BOLA)

| Task | Component | Description | Expected Behavior | Test Status |
|------|-----------|-------------|-------------------|-------------|
| T806 | Playlist RETRIEVE | Чтение чужого плейлиста | ✅ HOST **должен** видеть все плейлисты | ❌ Тесты падают (404) |
| T829 | SmartBlock RETRIEVE | Чтение чужого блока | ✅ HOST **должен** видеть все блоки | ❌ Тесты падают (404) |
| T830 | SmartBlock LIST | Просмотр всех блоков | ✅ HOST **должен** видеть все блоки | ❌ Тесты падают |
| T851 | File LIST | Просмотр всех файлов | ✅ HOST **должен** видеть все файлы | ❌ Тесты падают |
| T850 | File RETRIEVE | Чтение чужого файла | ✅ HOST **должен** видеть все файлы | ❌ Тесты падают (404) |
| T727 | Podcast RETRIEVE | Чтение чужого подкаста | ✅ HOST **должен** видеть все подкасты | ❌ Тесты падают (404) |
| T682 | PodcastEpisode LIST | Просмотр всех эпизодов | ✅ HOST **должен** видеть все эпизоды | Не проверено |

**Проблема:** Тесты `test_role_view_matrix.py`, `test_role_detail_matrix.py`, `test_role_host_permissions.py` ожидают что HOST видит всё, но получают 404.

---

## Type B: Tasks That ARE FIXED (Correctly Prevent BOLA)

Эти задачи **корректно пофикшены** и тесты должны проходить:

### MODIFY Operations (BOLA Prevention Works)

| Task | Component | Description | Fix Status | Test Status |
|------|-----------|-------------|------------|-------------|
| T808 | Playlist UPDATE | Изменение чужого плейлиста | ✅ FIXED | ✅ PASS |
| T809 | Playlist DELETE | Удаление чужого плейлиста | ✅ FIXED | ✅ PASS |
| T831 | SmartBlock UPDATE | Изменение чужого блока | ✅ FIXED | ✅ PASS |
| T832 | SmartBlock DELETE | Удаление чужого блока | ✅ FIXED | ✅ PASS |
| T853 | File DELETE | Удаление чужого файла | ✅ FIXED | Не проверено |
| T541 | Webstream UPDATE | Изменение чужого стрима | ✅ FIXED | ✅ PASS |
| T542 | Webstream DELETE | Удаление чужого стрима | ✅ FIXED | ✅ PASS |
| T592 | Schedule UPDATE | Изменение чужого расписания | ✅ FIXED | ✅ PASS |
| T598 | Schedule DELETE | Удаление чужого расписания | ✅ FIXED | ✅ PASS |
| T408 | ShowHost LIST | Просмотр всех назначений | ✅ FIXED (фильтрация по user) | ⚠️ Тесты не проверяли |

### CREATE with Validation (BOLA Prevention Works)

| Task | Component | Description | Fix Status |
|------|-----------|-------------|------------|
| T475 | SmartBlockContent CREATE | Создание в чужом блоке | ✅ FIXED - validate_block() |
| T476 | SmartBlockContent CREATE | Использование чужого файла | ✅ FIXED - validate_file() |
| T496 | SmartBlockCriteria CREATE | Создание для чужого блока | ✅ FIXED - validate_block() |
| T577 | Schedule CREATE | Использование чужого файла | ✅ FIXED - через File ForeignKey |
| T578 | Schedule CREATE | Использование чужого стрима | ✅ FIXED - через Webstream FK |

---

## Type C: Tests That BROKEN (Need Fix)

Эти тесты падают из-за несоответствия ожиданий и реализации:

### Broken VIEW Tests (43 failures)

```
test_role_view_matrix.py:
- test_guest_can_view_playlists
- test_guest_can_view_smartblocks
- test_guest_can_view_webstreams
- test_guest_can_view_podcasts
- test_guest_can_view_files
- test_host_can_view_all_playlists
- test_host_can_view_all_smartblocks
- test_host_can_view_all_webstreams
- test_host_can_view_all_files
- test_all_roles_see_same_content_for_view

test_role_detail_matrix.py:
- test_guest_can_retrieve_playlist_detail
- test_guest_can_retrieve_smartblock_detail
- test_guest_can_retrieve_webstream_detail
- test_guest_can_retrieve_podcast_detail
- test_guest_can_retrieve_file_detail
- test_host_can_retrieve_other_playlist_detail (14 tests)

test_role_host_permissions.py:
- test_host_can_retrieve_any_playlist
- test_host_can_retrieve_any_file
- test_host_can_retrieve_any_smartblock
- test_host_can_retrieve_any_webstream

test_role_guest_permissions.py:
- test_guest_can_retrieve_playlist
- test_guest_can_retrieve_file
- test_guest_can_retrieve_smartblock
- test_guest_can_retrieve_webstream
```

**Причина:** Все эти тесты ожидают 200 OK, но получают 404 из-за фильтрации в get_queryset().

---

## Root Cause Analysis

### The Design Conflict

**Permissions Inventory говорит:**
- GUEST: "view_all" permission - видит всё
- HOST: "view_all" + "change_own" + "delete_own" - видит всё, изменяет своё

**Но реализация:**
- Фильтрация в `get_queryset()` применяется ко ВСЕМ операциям (LIST, RETRIEVE, UPDATE, DELETE)
- Результат: RETRIEVE возвращает 404 для чужих объектов

### Как должно работать

```python
# Неправильно (текущая реализация):
def get_queryset(self):
    if user.role == HOST:
        return Model.objects.filter(owner=user)  # Ломает RETRIEVE

# Правильно (разделение):
def get_queryset(self):
    # LIST - фильтруем
    if self.action == 'list':
        return Model.objects.filter(owner=user)
    # RETRIEVE/UPDATE/DELETE - не фильтруем, permission_class решает
    return Model.objects.all()
```

ИЛИ

```python
# Использовать разные permission classes:
# - Для LIST: фильтрация в get_queryset()
# - Для RETRIEVE: obj-level permission check
```

---

## Recommendations

### Option 1: Fix get_queryset() to handle actions differently (RECOMMENDED)

```python
def get_queryset(self):
    queryset = super().get_queryset()
    
    # API-Key bypass
    if check_authorization_header(self.request):
        return queryset
    
    user = self.request.user
    if not user.is_authenticated:
        return queryset.none()
    
    if user.role in [ADMIN, MANAGER]:
        return queryset
    
    # For LIST: filter by owner
    if self.action == 'list':
        return queryset.filter(owner=user)
    
    # For RETRIEVE/UPDATE/DELETE: return all, permission check handles access
    return queryset
```

### Option 2: Use separate ViewSet methods

```python
def list(self, request, *args, **kwargs):
    # Custom list with filtering
    queryset = self.get_queryset().filter(owner=request.user)
    serializer = self.get_serializer(queryset, many=True)
    return Response(serializer.data)

def retrieve(self, request, *args, **kwargs):
    # Default retrieve - no filtering
    return super().retrieve(request, *args, **kwargs)
```

### Option 3: Fix tests to match new behavior (NOT RECOMMENDED)

Если решено что VIEW тоже должно фильтроваться - это ломает GUEST роль полностью.

---

## Tasks Summary by Status

### Truly Fixed (BOLA prevention works for MODIFY):
- T475, T476, T477, T481, T482, T483, T488, T489, T490, T491, T492
- T500, T502, T503, T505, T506, T507, T518, T541, T542
- T569, T587, T592, T598, T663
- T808, T809, T829, T830, T831, T832

### Still Open (from issues.md):
- T353 - Podcast ViewSets (need investigation)
- T358 - PlaylistContent Anonymous (need test)
- T362 - SmartBlock Anonymous filter
- T363 - SmartBlock kind filter
- T368 - SmartBlockCriteria Anonymous
- T369 - SmartBlockCriteria LIST
- T392 - ShowDays filter
- T390 - ShowDays BOLA
- T407 - ShowHosts LIST Anonymous
- T413 - Playlist owner filter
- T420 - Playlist ViewSet
- T425 - SmartBlock ViewSets
- T574 - Schedule filter combination
- T576 - Schedule CREATE for other show
- T612 - Schedule cross-instance
- T616 - Schedule overbooked filter
- T617, T618 - Schedule host operations
- T682 - PodcastEpisode LIST
- T854 - File download
- T863, T864 - Cascade delete
- T874, T889, T897, T901, T909 - File filters
- T383 - Show IDOR

### False Positives (Not BOLA, by design):
- T806, T829, T830, T850, T851, T727, T682

---

## Action Items

1. **CRITICAL:** Fix get_queryset() to not filter on RETRIEVE for GUEST/HOST
2. **HIGH:** Update test_role_view_matrix.py tests to expect filtered LIST for HOST
3. **HIGH:** Update test_role_detail_matrix.py tests to expect 200 for RETRIEVE
4. **MEDIUM:** Verify all MODIFY operations still correctly prevent BOLA
5. **LOW:** Document the permission model clearly for future reference
