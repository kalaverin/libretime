# BOLA Анализ - 77 задач

## Дата анализа: 2026-04-11

## Категоризация

### 1. УЖЕ ЗАЩИЩЕНО через permission system (требуют закрытия как DONE)

Ресурсы с `owner` полем защищены через `own_*` permissions:

| Ресурс | UPDATE чужого | DELETE чужого | Тесты |
|--------|---------------|---------------|-------|
| Playlist | ✅ 403 | ✅ 403 | test_role_update/delete_matrix |
| SmartBlock | ✅ 403 | ✅ 403 | test_role_update/delete_matrix |
| Webstream | ✅ 403 | ✅ 403 | test_role_update/delete_matrix |
| File | ✅ 403 | ✅ 403 | test_role_host_permissions |
| Podcast | ✅ 403 | ✅ 403 | test_role_create_matrix |

**Задачи для закрытия:**
- T541, T542 (Webstream UPDATE/DELETE) - DONE
- T505, T506 (SmartBlockCriteria UPDATE/DELETE) - частично (нет owner поля!)

### 2. Public by design (требуют решения - public или добавить private флаг)

LIST/RETRIEVE для broadcast schedule системы:

| Ресурс | Текущее поведение | Ожидаемое |
|--------|-------------------|-----------|
| Playlist LIST | Все видят все | Public ✅ |
| SmartBlock LIST | Все видят все | Public ✅ |
| Webstream LIST | Все видят все | Public ✅ |
| File LIST | Все видят все | Public ✅ |
| Podcast LIST | Все видят все | Public ✅ |
| SmartBlockCriteria LIST | Все видят все | Public ✅ |

**Задачи:** T488, T518, T353, T365, T366, T874 и др.

### 3. РЕАЛЬНЫЕ ПРОБЛЕМЫ (требуют фикса)

#### A. Nested Resources CREATE (без проверки parent.owner)

| Задача | Проблема | Фикс |
|--------|----------|------|
| T475 | SmartBlockContent CREATE в чужой блок | Сериализатор: проверить block.owner |
| T476 | SmartBlockContent CREATE с чужим файлом | Сериализатор: проверить file.owner |
| T496 | SmartBlockCriteria CREATE в чужой блок | Сериализатор: проверить block.owner |
| T358 | PlaylistContent CREATE в чужой плейлист | Сериализатор: проверить playlist.owner |

#### B. Block Takeover (изменение parent через UPDATE)

| Задача | Проблема | Фикс |
|--------|----------|------|
| T507 | SmartBlockCriteria block takeover | Запретить изменение block поля или проверять owner |
| T509 | SmartBlockCriteria PUT takeover | То же для PUT |

#### C. Resources без owner поля

| Ресурс | Проблема | Фикс |
|--------|----------|------|
| SmartBlockCriteria | Нет owner, связь через block | Проверять block.owner в perform_* |
| SmartBlockContent | Нет owner, связь через block | Проверять block.owner в perform_* |
| PlaylistContent | Нет owner, связь через playlist | Проверять playlist.owner в perform_* |

#### D. Special endpoints

| Задача | Проблема | Фикс |
|--------|----------|------|
| T892 | Stereo/mono endpoint | Добавить фильтрацию |
| T889 | File filter by import_status | Добавить фильтрацию |
| T901 | File organization | Добавить изоляцию |

### 4. ОТДЕЛЬНЫЕ СЛУЧАИ

#### T854 - File download (ИСПРАВЛЕНО)
- ✅ Fixed: добавлена проверка аутентификации
- Anonymous: 403
- Authenticated: 200 (public download)

## Приоритет фиксов

### P0 (Nested Resources - критично)
1. T475, T476 - SmartBlockContent CREATE
2. T496 - SmartBlockCriteria CREATE
3. T358 - PlaylistContent CREATE

### P1 (Block Takeover)
4. T507, T509 - SmartBlockCriteria takeover

### P2 (Resources без owner)
5. SmartBlockCriteria UPDATE/DELETE проверка
6. SmartBlockContent UPDATE/DELETE проверка

### P3 (LIST фильтрация - если нужно)
7. Добавить private флаг для ресурсов (опционально)

## Рекомендуемые действия

1. **Закрыть как DONE**: T541, T542 (Webstream защищен)
2. **Закрыть как NOT_NEEDED**: LIST задачи (public by design)
3. **Исправить**: Nested Resources CREATE (T475, T476, T496, T358)
4. **Исправить**: Block Takeover (T507, T509)
5. **Добавить проверки**: Для resources без owner поля
