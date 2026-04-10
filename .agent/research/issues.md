# Анализ задач безопасности (tasks.md)

**Сгенерирован:** 2026-04-10T21:57:20Z
**Всего задач:** ~6778 строк в tasks.md
**Активных задач (NOT_STARTED):** ~275+

---

## Сводная таблица по категориям

| Категория | CRITICAL | HIGH | MEDIUM | LOW | Всего |
|-----------|----------|------|--------|-----|-------|
| BOLA (API1:2023) | 35+ | 25+ | 10 | 2 | ~72 |
| BOPLA (API3:2023) | 15+ | 35+ | 40+ | 5 | ~95 |
| XSS (Stored/Reflected) | 12 | 18 | 10 | - | ~40 |
| SSRF | 8 | 6 | 4 | - | ~18 |
| Path Traversal/LFI | 8 | 10 | 4 | - | ~22 |
| Auth Bypass | 15+ | 8 | 10 | 4 | ~37 |
| Rate Limiting (API4:2023) | 2 | 15+ | 35+ | 5 | ~57 |
| SQL Injection (API8:2023) | 4 | 8 | 6 | - | ~18 |
| Info Disclosure | 5 | 12 | 15 | 5 | ~37 |
| Input Validation | 3 | 18 | 25+ | 8 | ~54 |
| Race Conditions | 2 | 5 | 8 | 3 | ~18 |
| Cryptography/Passwords | 5 | 8 | 6 | 3 | ~22 |
| Test Infrastructure | - | 5 | 40+ | 45+ | ~90 |
| SDK/Code Fixes | 8 | 15 | 10 | 5 | ~38 |
| API Bug Fixes | 5 | 12 | 15 | 8 | ~40 |

---

## Категория 1: BOLA (Broken Object Level Authorization) — API1:2023

**Паттерн:** Отсутствие фильтрации queryset по owner, доступ к чужим данным по ID

| ID | Компонент | Описание |
|----|-----------|----------|
| T475 | SmartBlockContent CREATE | Создание контента в чужом блоке |
| T476 | SmartBlockContent CREATE | Использование чужого файла |
| T488 | SmartBlockCriteria LIST | Просмотр критериев всех пользователей |
| T489 | SmartBlockCriteria filter | Обход через фильтр по block |
| T496 | SmartBlockCriteria CREATE | Создание критериев для чужого блока |
| T505 | SmartBlockCriteria UPDATE | Изменение чужих критериев |
| T506 | SmartBlockCriteria DELETE | Удаление чужих критериев |
| T507 | SmartBlockCriteria UPDATE | Перенос критериев в чужой блок |
| T518 | Webstreams LIST | Просмотр всех вебстримов |
| T541 | Webstream UPDATE | Изменение чужого стрима |
| T542 | Webstream DELETE | Удаление чужого стрима |
| T563 | Webstream DELETE | BOLA delete (повтор) |
| T562 | Webstream UPDATE | BOLA update (повтор) |
| T564 | Webstreams LIST | BOLA list (повтор) |
| T568 | Schedule LIST | Просмотр всех расписаний |
| T569 | Schedule RETRIEVE | Доступ к чужому по ID |
| T574 | Schedule filter | Обход через комбинацию фильтров |
| T576 | Schedule CREATE | Создание для чужого шоу |
| T577 | Schedule CREATE | Использование чужого файла |
| T578 | Schedule CREATE | Использование чужого стрима |
| T587 | Schedule RETRIEVE | Чтение чужого расписания |
| T592 | Schedule UPDATE | Изменение чужого расписания |
| T598 | Schedule DELETE | Удаление чужого расписания |
| T612 | Schedule cross-instance | Доступ между инстансами |
| T616 | Schedule overbooked | Утечка через фильтр |
| T617 | Schedule host | Хост меняет чужое шоу |
| T618 | Schedule host | Хост удаляет чужое шоу |
| T663 | Podcast LIST | Просмотр всех подкастов |
| T682 | PodcastEpisode LIST | Просмотр всех эпизодов |
| T727 | Podcast RETRIEVE | Чтение чужого подкаста |
| T806 | Playlist RETRIEVE | Чтение чужого плейлиста |
| T807 | Playlist LIST | Просмотр всех плейлистов |
| T808 | Playlist UPDATE | Изменение чужого плейлиста |
| T809 | Playlist DELETE | Удаление чужого плейлиста |
| T829 | SmartBlock RETRIEVE | Чтение чужого блока |
| T830 | SmartBlock LIST | Просмотр всех блоков |
| T831 | SmartBlock UPDATE | Изменение чужого блока |
| T832 | SmartBlock DELETE | Удаление чужого блока |
| T850 | File RETRIEVE | Чтение чужого файла |
| T851 | File LIST | Просмотр всех файлов |
| T853 | File DELETE | Удаление чужого файла |
| T854 | File download | Скачивание чужого файла |
| T863 | Show DELETE | Каскадное удаление шоу |
| T864 | Playlist DELETE | Каскадное удаление плейлиста |
| T874 | File/Playlist LIST | Глобальная утечка |
| T889 | File filter | Утечка через import_status |
| T897 | File filter | Утечка через channels |
| T901 | File organization | BOLA в организации |
| T909 | File filter | Утечка через фильтры |
| T383 | Show IDOR | Доступ к чужому шоу |
| T412 | Playlist BOLA | Просмотр чужих плейлистов |
| T408 | ShowHost LIST | Просмотр всех назначений |
| T392 | ShowDays filter | Обход через show_id |
| T390 | ShowDays BOLA | Фильтр без проверки |
| T407 | ShowHosts LIST | Просмотр без авторизации |
| T413 | Playlist owner filter | Обход через owner_id |
| T353 | Podcast ViewSets | Отсутствие фильтрации |
| T420 | Playlist ViewSet | Отсутствие фильтрации |
| T425 | SmartBlock ViewSets | Отсутствие фильтрации |
| T358 | PlaylistContent | Anonymous BOLA |
| T362 | SmartBlock | Anonymous filter |
| T363 | SmartBlock kind | Фильтр показывает все |
| T368 | SmartBlockCriteria | Anonymous access |
| T369 | SmartBlockCriteria LIST | Показывает все критерии |
| T875 | File owner filter | Обход через owner_id |

---

## Категория 2: BOPLA (Broken Object Property Level Authorization) — API3:2023

**Паттерн:** Mass assignment, изменение системных полей (id, owner, created_at, timestamps)

| ID | Поле | Компонент | Описание |
|----|------|-----------|----------|
| T477 | id | SmartBlockContent | Массовое присвоение ID |
| T497 | id | SmartBlockCriteria | ID в CREATE |
| T508 | id | SmartBlockCriteria | ID в UPDATE |
| T547 | id | Webstream | ID манипуляции |
| T810 | id | Playlist | ID присвоение |
| T833 | id | SmartBlock | ID присвоение |
| T858 | id | File | ID присвоение |
| T426 | id | SmartBlock CREATE | Mass assignment |
| T526 | owner | Webstream CREATE | Чужой владелец |
| T546 | owner | Webstream UPDATE | Смена владельца |
| T567 | owner | Webstream UPDATE | Передача владения |
| T812 | owner | Playlist | Смена владельца |
| T835 | owner | SmartBlock | Смена владельца |
| T860 | owner | File | Смена владельца |
| T880 | owner | Playlist | Mass assignment |
| T882 | owner | File metadata | Mass assignment |
| T904 | library | File | Библиотечный хайджекинг |
| T428 | owner | SmartBlock CREATE | BOLA vector |
| T438 | owner | SmartBlock PATCH | Block hijacking |
| T529 | created_at | Webstream | Манипуляция timestamp |
| T548 | created_at | Webstream UPDATE | Установка времени |
| T811 | created_at | Playlist | Присвоение времени |
| T834 | created_at | SmartBlock | Присвоение времени |
| T859 | created_at | File | Присвоение времени |
| T427 | created_at | SmartBlock | Backdating |
| T439 | created_at | SmartBlock PATCH | Backdating |
| T431 | updated_at | SmartBlock | Future timestamp |
| T440 | updated_at | SmartBlock PATCH | Future time |
| T478 | extra fields | SmartBlockContent | Приём лишних полей |
| T498 | extra fields | SmartBlockCriteria | Приём лишних |
| T530 | extra fields | Webstream | Приём лишних |
| T813 | extra fields | Playlist | Приём лишних |
| T836 | extra fields | SmartBlock | Приём лишних |
| T861 | extra fields | File | Приём лишних |
| T703 | extra fields | Podcast | Приём лишних |
| T730 | extra fields | Podcast PATCH | Приём лишних |
| T373 | token | UserToken | Мутация токена |
| T374 | attempts | LoginAttempt | Манипуляция счётчиком |
| T655 | end_time | LiveLog | Фальсификация времени |
| T647 | count | ListenerCount | Манипуляция статистикой |
| T419 | created_at | Playlist | Mutable timestamp |
| T887 | import_status | File | Workflow bypass |
| T891 | import_status | File | PENDING→SUCCESS bypass |
| T905 | import_status | File | Workflow manipulation |
| T888 | channels | File | Экстремальные значения |
| T894 | channels | File | Validation missing |
| T900 | channels | File | Negative values |
| T893 | channels | File | Mass assignment |
| T895 | sample_rate | File | Mass assignment |
| T480 | position | SmartBlockContent | Дубликаты позиций |
| T481 | offset | SmartBlockContent | Отрицательные значения |
| T482 | cue_out/cue_in | SmartBlockContent | cue_out < cue_in |
| T483 | cue format | SmartBlockContent | Невалидный формат |
| T499 | value | SmartBlockCriteria | Слишком длинные |
| T500 | group | SmartBlockCriteria | Отрицательные |
| T502 | criteria | SmartBlockCriteria | Невалидные типы |
| T503 | condition | SmartBlockCriteria | Невалидные условия |
| T510 | value | SmartBlockCriteria UPDATE | Пустые значения |
| T511 | value | SmartBlockCriteria UPDATE | Слишком длинные |
| T536 | name | Webstream | Length validation |
| T537 | name | Webstream | Empty name |
| T553 | name | Webstream UPDATE | Empty name |
| T641 | template | TemplateField | Чужой template |
| T626 | history | PlayoutHistory metadata | Чужая история |

---

## Категория 3: XSS — Stored & Reflected

| ID | Поле | Компонент | Тип |
|----|------|-----------|-----|
| T521 | MIME type | Webstream | Stored |
| T525 | description | Webstream | Stored |
| T534 | name | Webstream | Stored |
| T535 | description | Webstream | Stored |
| T549 | name | Webstream UPDATE | Stored |
| T550 | description | Webstream UPDATE | Stored |
| T402 | description | ShowInstances | Stored |
| T379 | url | Show | Reflected |
| T380 | description | Show | Stored |
| T385 | url | Show PATCH | Reflected |
| T386 | description | Show PATCH | Stored |
| T629 | key | PlayoutHistory metadata | Stored |
| T630 | value | PlayoutHistory metadata | Stored |
| T635 | name | Template | Stored |
| T636 | type | Template | Stored |
| T642 | name | TemplateField | Stored |
| T643 | label | TemplateField | Stored |
| T659 | state | LiveLog | Stored |
| T708 | title | Podcast | Stored |
| T709 | description | Podcast | Stored |
| T710 | itunes_* | Podcast | Stored |
| T732 | title | Podcast UPDATE | Stored |
| T733 | description | Podcast PATCH | Stored |
| T883 | track_title | File metadata | Stored |
| T534 | name | Webstream | Stored |
| T535 | description | Webstream | Stored |

---

## Категория 4: SSRF (Server-Side Request Forgery)

| ID | Вектор | Компонент | Описание |
|----|--------|-----------|----------|
| T29 | URL | Podcast download | file://, internal URLs |
| T520 | URL | Webstream LIST | Internal reflection |
| T523 | URL | Webstream | Invalid URL accepted |
| T531 | URL | Webstream CREATE | Internal URL accepted |
| T532 | URL | Webstream CREATE | Cloud metadata |
| T544 | URL | Webstream UPDATE | Update to internal |
| T545 | URL | Webstream UPDATE | Cloud metadata update |
| T551 | URL | Webstream PUT | Dangerous URL |
| T583 | stream | Schedule CREATE | Internal stream |
| T596 | stream | Schedule UPDATE | Internal stream update |

---

## Категория 5: Path Traversal / LFI

| ID | Поле | Компонент | Описание |
|----|------|-----------|----------|
| T7 | filepath | FileViewSet download | Path traversal |
| T8 | filepath | FileViewSet destroy | Path traversal |
| T479 | cue_in/out | SmartBlockContent | Path patterns |
| T855 | filepath | File CREATE | Traversal patterns |
| T856 | filepath | File UPDATE | Traversal via PATCH |
| T886 | filepath | File | Traversal accepted |
| T890 | filepath | File | Absolute paths |
| T857 | filepath | File | Absolute path accepted |

---

## Категория 6: Authentication Bypass / Auth Issues

| ID | Проблема | Компонент | Описание |
|----|----------|-----------|----------|
| T354 | Anonymous | Webstream | created_at mutable |
| T360 | Anonymous | PlaylistContent | Filter access |
| T362 | Anonymous | SmartBlock | Filter access |
| T364 | Anonymous | Schedule | Filter access |
| T378 | Anonymous | Show | CREATE access |
| T382 | Anonymous | Show | RETRIEVE access |
| T384 | Anonymous | Show | UPDATE access |
| T387 | Anonymous | Show | DELETE access |
| T391 | Anonymous | ShowDays | CREATE access |
| T411 | Anonymous | Playlist | LIST access |
| T575 | Invalid token | Schedule LIST | 200 on invalid |
| T584 | Invalid token | Schedule CREATE | 200 on invalid |
| T589 | Invalid token | Schedule RETRIEVE | 200 on invalid |
| T597 | Invalid token | Schedule UPDATE | 200 on invalid |
| T600 | Invalid token | Schedule DELETE | 200 on invalid |
| T376 | Unicode | Auth header | UnicodeEncodeError |
| T749 | Unicode | API Key | 500 error |
| T793 | Unicode | Auth header | Unhandled exception |
| T459 | Case sensitivity | Auth header | Case-sensitive parsing |
| T753 | Case sensitivity | Authorization | Case-sensitive reject |
| T460 | Empty token | Auth | Empty/malformed |
| T912 | Newline | API Key | Header injection \\n |
| T913 | CR | API Key | Header injection \\r |
| T740 | Account lockout | Auth | No lockout after fails |
| T783 | Brute force | Password | No rate limiting |
| T784 | Brute force | API Key | No CAPTCHA/blocking |
| T745 | BFLA | Guest | Access to protected |
| T653 | BFLA | Guest | Live logs access |
| T664 | BFLA | Guest | Podcast LIST |
| T377 | Token revocation | Auth | Delay in revocation |
| T755 | Token expiration | API Key | No expiration |
| T756 | Token scope | API Key | User endpoints access |

---

## Категория 7: Rate Limiting / Resource Exhaustion — API4:2023

| ID | Эндпоинт | Проблема |
|----|----------|----------|
| T20 | API общий | Нет rate limiting |
| T47 | Celery | Нет max_instances |
| T424 | PlaylistContent | Нет rate limiting CREATE |
| T601 | Schedule DELETE | Нет rate limiting |
| T620 | PlayoutHistory LIST | Нет rate limiting |
| T623 | PlayoutHistory CREATE | Нет rate limiting |
| T631 | TemplateField CREATE | Нет rate limiting |
| T637 | Template CREATE | Нет rate limiting |
| T638 | Template UPDATE | Нет rate limiting |
| T645 | TemplateField CREATE | Нет rate limiting |
| T649 | ListenerCount CREATE | Нет rate limiting |
| T660 | LiveLog CREATE | Нет rate limiting |
| T662 | LiveLog UPDATE | Нет rate limiting |
| T678 | Podcast LIST | Нет rate limiting |
| T713 | Podcast CREATE | Нет rate limiting |
| T735 | Podcast UPDATE | Нет rate limiting |
| T736 | Podcast DELETE | Нет rate limiting |
| T750 | API Key auth | Нет rate limiting |
| T752 | API Key length | DoS long keys |
| T769 | Public endpoints | Нет rate limiting |
| T783 | Password auth | Нет rate limiting |
| T784 | API Key brute force | Нет CAPTCHA |
| T862 | File CREATE | Нет rate limiting |
| T869 | Cascade delete | Нет rate limiting |
| T823 | Playlist CREATE | Нет rate limiting |
| T876 | API LIST | Resource exhaustion |
| T881 | All updates | No optimistic locking |

---

## Категория 8: SQL Injection — API8:2023

| ID | Параметр | Компонент | Описание |
|----|----------|-----------|----------|
| T490 | block filter | SmartBlockCriteria | SQLi в block_id |
| T356 | block_id | SmartBlockContent | Invalid ID → 500 |
| T357 | playlist_id | PlaylistContent | Invalid ID → 500 |
| T367 | block_id | SmartBlockCriteria | Filter crash |
| T613 | overbooked | Schedule | SQLi в фильтре |
| T814 | length | Playlist | SQLi в length field |

---

## Категория 9: Information Disclosure / Error Leaks

| ID | Утечка | Компонент | Описание |
|----|--------|-----------|----------|
| T493 | DB structure | SmartBlockCriteria | Название таблицы |
| T849 | DB structure | SmartBlock | cc_block в ошибке |
| T514 | Existence | SmartBlockCriteria | 404 vs 403 |
| T558 | Existence | Webstream | Error diff leak |
| T543 | Existence | Webstream | Error messages |
| T602 | Existence | Schedule DELETE | Status diff |
| T591 | Existence | Schedule RETRIEVE | Error codes |
| T573 | Existence | Schedule LIST | Message leak |
| T673 | Owner ID | Podcast LIST | User enumeration |
| T675 | Status codes | Podcast | IDOR через статусы |
| T400 | Query keyword | ShowInstances | Django ORM leak |
| T910 | Timing | File | Timing attack |
| T493 | SQL details | SmartBlockCriteria | SQL в ошибке |

---

## Категория 10: Input Validation / Business Logic

| ID | Проблема | Компонент | Описание |
|----|----------|-----------|----------|
| T481 | Negative offset | SmartBlockContent | Отрицательный offset |
| T500 | Negative group | SmartBlockCriteria | Отрицательный group |
| T648 | Negative count | ListenerCount | Отрицательный count |
| T644 | Negative position | TemplateField | Отрицательная позиция |
| T900 | Negative channels | File | Отрицательные каналы |
| T482 | Time order | SmartBlockContent | cue_out < cue_in |
| T483 | Time format | SmartBlockContent | Невалидный формат |
| T817 | Time format | Playlist | Невалидный length |
| T381 | Color format | Show | Невалидный hex |
| T522 | Length overflow | Webstream | URL length |
| T536 | Length overflow | Webstream | Name length |
| T818 | Length overflow | Playlist | Length value |
| T499 | Length overflow | SmartBlockCriteria | Value length |
| T502 | Invalid choices | SmartBlockCriteria | Невалидный criteria |
| T503 | Invalid condition | SmartBlockCriteria | Невалидный condition |
| T837 | Invalid kind | SmartBlock | Невалидный kind |
| T441 | Invalid kind | SmartBlock PATCH | Invalid values |
| T581 | Schedule overlap | Schedule | Пересечение |
| T595 | Schedule overlap | Schedule UPDATE | Overlap via update |
| T582 | Time boundaries | Schedule | Вне границ шоу |
| T656 | Time range | LiveLog | end < start |
| T657 | Future time | LiveLog | Future start_time |
| T651 | Future timestamp | ListenerCount | Future timestamp |
| T443 | Null required | SmartBlock | Null for required |
| T396 | Null last_show | ShowDays | Null removal |
| T395 | Negative duration | ShowDays | Отрицательная длительность |

---

## Категория 11: Race Conditions

| ID | Операция | Компонент | Описание |
|----|----------|-----------|----------|
| T12 | queue popleft | playout/player/queue | Race в deque |
| T30 | organise_file | analyzer/pipeline | TOCTOU |
| T486 | Concurrent CREATE | SmartBlockContent | Дубликаты |
| T504 | Concurrent CREATE | SmartBlockCriteria | Race condition |
| T515 | Concurrent DELETE | SmartBlockCriteria | Race |
| T539 | Concurrent CREATE | Webstream | Дубликаты |
| T555 | Concurrent UPDATE | Webstream | Lost updates |
| T586 | Concurrent CREATE | Schedule | Same slot race |
| T559 | Concurrent DELETE | Webstream | Race |
| T433 | Duplicate names | SmartBlock | Race на имена |
| T722 | Duplicate podcasts | Podcast | Concurrent creation |

---

## Категория 12: Cryptography / Password Security

| ID | Проблема | Компонент | Описание |
|----|----------|-----------|----------|
| T5 | MD5 hashing | User model | Устаревший MD5 |
| T22 | Plain text | Show model | live_auth_custom_password |
| T370 | Password exposure | Show serializer | Пароль в API ответе |
| T741 | Weak passwords | User model | 123456 accepted |
| T742 | Common passwords | User model | wordlist passwords |
| T743 | Short passwords | User model | < 8 chars accepted |
| T916 | Short API key | Settings | testing key too short |
| T917 | Short SECRET_KEY | Settings | 33 chars too short |

---

## Категория 13: Test Infrastructure (Legacy PHP)

| ID | Компонент | Описание | Phase |
|----|-----------|----------|-------|
| T66 | TestBootstrap | Unified entry point | 0 |
| T67 | phpunit.xml | Bootstrap config | 0 |
| T68 | TestHelper | getDbZendConfig | 0 |
| T69 | TestHelper | installTestDatabase | 0 |
| T70 | AirtimeInstall | CreateDatabaseTables | 0 |
| T71 | ModelFactory | Test fixtures | 0 |
| T72-T74 | YAML fixtures | User/Show/File fixtures | 0 |
| T75-T79 | DateHelper | Date/time methods | 1 |
| T80-T84 | FileDataHelper | File operations | 1 |
| T85-T87 | HTTPHelper | HTTP utilities | 1 |
| T88-T91 | SecurityHelper | Security functions | 1 |
| T92 | LocaleHelper | Localization | 1 |
| T93 | OsPath | Path utilities | 1 |
| T94 | Timezone | Timezone handling | 1 |
| T95-T104 | ShowService | Show operations | 2 |
| T105 | ShowService | Private methods | 2 |
| T106 | SchedulerService | Scheduling | 2 |
| T107-T108 | UserService | User CRUD/auth | 2 |
| T109 | MediaService | File operations | 2 |
| T110 | PodcastService | Podcast methods | 2 |
| T111-T115 | Models | Show/Instance/Schedule | 3 |
| T116 | Block Model | Smart blocks | 3 |
| T117 | Playlist Model | Playlist CRUD | 3 |
| T118 | StoredFile Model | File metadata | 3 |
| T119 | User Model | User auth | 3 |
| T120 | Preference Model | System prefs | 3 |
| T121 | Library Model | Library browse | 3 |
| T122 | Webstream Model | Webstream CRUD | 3 |
| T123-T127 | Forms | Validation forms | 4 |
| T128-T130 | Auth/ACL | Authentication | 5 |
| T131-T136 | Controllers | All controllers | 6 |
| T137-T143 | Integration | E2E scenarios | 7 |
| T144-T147 | REST | REST endpoints | 8 |
| T148-T152 | Coverage/Docs | Documentation | 10 |

---

## Категория 14: SDK/Code Fixes

| ID | Проблема | Файл | Уровень |
|----|----------|------|---------|
| T2 | Unreachable code | sdk/logging.py | CRITICAL |
| T3 | SSL verify=False | sdk/http/client.py | CRITICAL |
| T4 | Passwords in URL | api_client/v1.py | CRITICAL |
| T9 | File descriptor leak | worker/tasks.py | CRITICAL |
| T10 | Mutable class state | analyzer/status_reporter.py | CRITICAL |
| T11 | Infinite loop | playout/liquidsoap/client.py | CRITICAL |
| T13 | Pickle → JSON | analyzer/status_reporter.py | CRITICAL |
| T14 | Timer leak | playout/player/fetch.py | CRITICAL |
| T15 | No timeout | analyzer/status_reporter.py | CRITICAL |
| T16 | Silent failure | api_client/v1.py | CRITICAL |
| T17 | sys.exit in lib | sdk/config/_base.py | CRITICAL |
| T18 | No transaction | api/storage/views/file.py | HIGH |
| T19 | __all__ in serializers | Multiple | HIGH |
| T23 | Mutable class var | sdk/http/client.py | HIGH |
| T24 | Unbounded cache | sdk/http/client.py | HIGH |
| T25 | Session not closed | api_client/_client.py | HIGH |
| T26 | Empty response | playout/liquidsoap/client.py | HIGH |
| T27 | Infinite loop | playout/liquidsoap/client.py | HIGH |
| T28 | No graceful shutdown | Multiple player files | HIGH |
| T31 | Error ignored | analyzer/pipeline/analyze_cuepoint.py | HIGH |
| T32 | PIPE deadlock | analyzer/pipeline/_utils.py | HIGH |
| T33 | File existence | analyzer/pipeline/analyze_metadata.py | HIGH |
| T34 | IndexError | api/permissions.py | HIGH |
| T35 | User comparison | api/permissions.py | HIGH |
| T36 | Auth header logging | api/middlewares.py | MEDIUM |
| T37 | URL validation | api/podcasts/models.py | MEDIUM |
| T38 | Uninitialized var | playout/player/queue.py | MEDIUM |
| T39 | API validation | playout/player/schedule.py | MEDIUM |
| T40 | Signal redefinition | playout/message_handler.py | MEDIUM |
| T41 | No rollback | analyzer/pipeline/pipeline.py | MEDIUM |
| T42 | Thread safety | playout/player/liquidsoap.py | MEDIUM |
| T43 | Locking cache | sdk/http/client.py | MEDIUM |
| T44 | Logger iteration race | sdk/structlog.py | MEDIUM |
| T45 | Exception args order | sdk/http/exceptions.py | MEDIUM |
| T46 | Falsy value handling | sdk/config/_base.py | MEDIUM |
| T48 | N+1 queries | Multiple models | MEDIUM |
| T49 | CSRF protection | api/settings/_internal.py | MEDIUM |
| T50 | Session not closed | playout/history/stats.py | MEDIUM |
| T52 | Unused import | api/storage/views/file.py | LOW |
| T53 | Deprecated Celery | worker/config.py | LOW |
| T54 | MD5 → SHA256 | sdk/files.py | LOW |
| T55 | Duplicate in __all__ | sdk/__init__.py | LOW |
| T56 | Typing inconsistency | api-client | LOW |
| T57 | Variable scoping | playout/player/fetch.py | LOW |

---

## Категория 15: Тестовые фиксы (Python)

| ID | Проблема | Файл | Статус |
|----|----------|------|--------|
| T58 | UTC.dst returns None | test_compat.py | NOT_STARTED |
| T59 | Max time milliseconds | test_datetime.py | NOT_STARTED |
| T60 | Config merge coercion | test_base.py | NOT_STARTED |
| T61 | Import error | test_models.py | NOT_STARTED |
| T62 | Env loader tests | test_env.py | NOT_STARTED |
| T63 | Fields validation | test_fields.py | NOT_STARTED |

---

## Категория 16: API Bug Fixes (Django/Django REST Framework)

| ID | Проблема | Компонент | Статус |
|----|----------|-----------|--------|
| T309 | Role filtering | UserViewSet | NOT_STARTED |
| T310 | API Key access | Permissions | NOT_STARTED |
| T315 | db_column | CeleryTask | NOT_STARTED |
| T316 | Missing instance.delete() | FileViewSet | NOT_STARTED |
| T317 | None filepath | FileViewSet.download | NOT_STARTED |
| T318 | FK constraint | Library DELETE | NOT_STARTED |
| T320 | Duplicate ShowHost | ShowHost model | NOT_STARTED |
| T321 | Null owner | Playlist CREATE | NOT_STARTED |
| T337 | Datetime comparison | Schedule model | NOT_STARTED |
| T338 | Host permissions | Schedule CREATE | NOT_STARTED |
| T352 | ends_at saving | Schedule serializer | NOT_STARTED |
| T355 | Null validation | SmartBlockContent | NOT_STARTED |
| T356 | Invalid block_id | SmartBlockContent | NOT_STARTED |
| T357 | Invalid playlist_id | PlaylistContent | NOT_STARTED |
| T358 | BOLA | PlaylistContent | NOT_STARTED |
| T359 | Playlist transferable | PlaylistContent | NOT_STARTED |
| T360 | Anonymous filter | PlaylistContent | NOT_STARTED |
| T361 | Invalid formats | PlaylistContent | NOT_STARTED |
| T362 | Anonymous filter | SmartBlock | NOT_STARTED |
| T363 | Kind filter BOLA | SmartBlock | NOT_STARTED |
| T364 | Anonymous filter | Schedule | NOT_STARTED |
| T365 | LIST BOLA | Schedule | NOT_STARTED |
| T366 | LIST BOLA | PlayoutHistory | NOT_STARTED |
| T367 | Invalid block_id | SmartBlockCriteria | NOT_STARTED |
| T368 | Anonymous filter | SmartBlockCriteria | NOT_STARTED |
| T369 | LIST BOLA | SmartBlockCriteria | NOT_STARTED |
| T370 | Password exposure | Show serializer | NOT_STARTED |
| T371 | User transferable | Preference | NOT_STARTED |
| T372 | LIST BOLA | Preference | NOT_STARTED |
| T373 | Token mutable | UserToken | NOT_STARTED |
| T374 | Counter mutable | LoginAttempt | NOT_STARTED |
| T375 | Deletable record | LoginAttempt | NOT_STARTED |
| T376 | Unicode crash | API Key | NOT_STARTED |
| T377 | Revocation delay | Token | NOT_STARTED |
| T388 | Anonymous LIST | ShowDays | OPEN |
| T389 | BOLA | ShowDays | OPEN |
| T390 | Filter bypass | ShowDays | OPEN |
| T391 | Anonymous CREATE | ShowDays | OPEN |
| T392 | repeat_next_on mutable | ShowDays | OPEN |
| T395 | Negative duration | ShowDays | OPEN |
| T396 | last_show_on null | ShowDays | OPEN |
| T400 | 404 leakage | ShowInstances | OPEN |
| T402 | XSS | ShowInstances | OPEN |
| T407 | Anonymous LIST | ShowHosts | OPEN |
| T408 | BOLA | ShowHosts | OPEN |
| T411 | Anonymous LIST | Playlists | OPEN |
| T412 | BOLA | Playlists | OPEN |
| T413 | Owner filter bypass | Playlists | OPEN |
| T419 | created_at mutable | Playlists | OPEN |
| T420 | BOLA | Playlist ViewSet | NOT_STARTED |
| T421 | 500 on invalid filter | PlaylistContent | NOT_STARTED |
| T422 | IntegrityError | PlaylistContent | NOT_STARTED |
| T423 | Negative position | PlaylistContent | NOT_STARTED |
| T424 | Rate limiting | PlaylistContent | NOT_STARTED |
| T425 | BOLA | SmartBlock ViewSets | NOT_STARTED |
| T426 | Mass assignment id | SmartBlock | NOT_STARTED |
| T427 | Mass assignment created_at | SmartBlock | NOT_STARTED |
| T428 | Mass assignment owner | SmartBlock | NOT_STARTED |
| T431 | Mass assignment updated_at | SmartBlock | NOT_STARTED |
| T432 | Arbitrary length | SmartBlock | NOT_STARTED |
| T433 | Race duplicate names | SmartBlock | NOT_STARTED |
| T434 | PATCH other user | SmartBlock | NOT_STARTED |
| T435 | PUT other user | SmartBlock | NOT_STARTED |
| T438 | Owner hijacking | SmartBlock | NOT_STARTED |
| T439 | Backdate created_at | SmartBlock | NOT_STARTED |
| T440 | Future updated_at | SmartBlock | NOT_STARTED |
| T441 | Invalid kind PATCH | SmartBlock | NOT_STARTED |
| T443 | Null required PUT | SmartBlock | NOT_STARTED |
| T444 | DELETE other user | SmartBlock | NOT_STARTED |
| T445 | Cascade delete | SmartBlock | NOT_STARTED |
| T446 | Existence leak | SmartBlock | NOT_STARTED |
| T447 | HTTP Method Override | SmartBlock | NOT_STARTED |
| T448 | LIST BOLA | SmartBlock | NOT_STARTED |
| T449 | RETRIEVE BOLA | SmartBlock | NOT_STARTED |
| T450 | ID enumeration | SmartBlock | NOT_STARTED |
| T451 | Bulk delete | SmartBlock | NOT_STARTED |
| T453 | Import endpoint | SmartBlock | NOT_STARTED |
| T454 | HOST privesc | SmartBlock | NOT_STARTED |
| T455 | DJ role bypass | SmartBlock | NOT_STARTED |
| T456 | Guest access | SmartBlock | NOT_STARTED |
| T458 | Role escalation | User | NOT_STARTED |
| T459 | Case-insensitive auth | Auth | NOT_STARTED |
| T460 | Empty token auth | Auth | NOT_STARTED |
| T461 | LIST BOLA | SmartBlockContent | NOT_STARTED |
| T462 | Filter bypass | SmartBlockContent | NOT_STARTED |
| T464 | SQLi block filter | SmartBlockContent | NOT_STARTED |
| T472 | 500 non-numeric | SmartBlockContent | NOT_STARTED |
| T473 | 500 unicode | SmartBlockContent | NOT_STARTED |
| T474 | 500 special params | SmartBlockContent | NOT_STARTED |
| T475 | BOLA CREATE block | SmartBlockContent | NOT_STARTED |
| T476 | BOLA CREATE file | SmartBlockContent | NOT_STARTED |
| T477 | BOPLA id | SmartBlockContent | NOT_STARTED |
| T478 | BOPLA extra fields | SmartBlockContent | NOT_STARTED |
| T479 | Path traversal cues | SmartBlockContent | NOT_STARTED |
| T480 | Duplicate position | SmartBlockContent | NOT_STARTED |
| T481 | Negative offset | SmartBlockContent | NOT_STARTED |
| T482 | cue_out before cue_in | SmartBlockContent | NOT_STARTED |
| T483 | Invalid cue format | SmartBlockContent | NOT_STARTED |
| T484 | Invalid token | Auth | NOT_STARTED |
| T485 | Wrong Content-Type | SmartBlockContent | NOT_STARTED |
| T486 | Race condition | SmartBlockContent | NOT_STARTED |
| T487 | JSON Merge Patch | SmartBlockContent | NOT_STARTED |
| T488 | BOLA LIST criteria | SmartBlockCriteria | NOT_STARTED |
| T489 | BOLA filter block | SmartBlockCriteria | NOT_STARTED |
| T490 | SQLi block param | SmartBlockCriteria | NOT_STARTED |
| T491 | 500 non-numeric | SmartBlockCriteria | NOT_STARTED |
| T492 | 500 unicode | SmartBlockCriteria | NOT_STARTED |
| T493 | Error leak structure | SmartBlockCriteria | NOT_STARTED |
| T494 | 500 special params | SmartBlockCriteria | NOT_STARTED |
| T495 | Criteria leak info | SmartBlockCriteria | NOT_STARTED |
| T496 | BOLA CREATE | SmartBlockCriteria | NOT_STARTED |
| T497 | BOPLA id | SmartBlockCriteria | NOT_STARTED |
| T498 | BOPLA extra fields | SmartBlockCriteria | NOT_STARTED |
| T499 | Overflow value | SmartBlockCriteria | NOT_STARTED |
| T500 | Negative group | SmartBlockCriteria | NOT_STARTED |
| T501 | Duplicate criteria | SmartBlockCriteria | NOT_STARTED |
| T502 | Invalid criteria type | SmartBlockCriteria | NOT_STARTED |
| T503 | Invalid condition | SmartBlockCriteria | NOT_STARTED |
| T504 | Race condition | SmartBlockCriteria | NOT_STARTED |
| T505 | BOLA UPDATE | SmartBlockCriteria | NOT_STARTED |
| T506 | BOLA DELETE | SmartBlockCriteria | NOT_STARTED |
| T507 | Block takeover | SmartBlockCriteria | NOT_STARTED |
| T508 | BOPLA id UPDATE | SmartBlockCriteria | NOT_STARTED |
| T509 | PUT block takeover | SmartBlockCriteria | NOT_STARTED |
| T510 | Empty value | SmartBlockCriteria | NOT_STARTED |
| T511 | Long value | SmartBlockCriteria | NOT_STARTED |
| T512 | DELETE status | SmartBlockCriteria | NOT_STARTED |
| T513 | Batch delete | SmartBlockCriteria | NOT_STARTED |
| T514 | Error leak existence | SmartBlockCriteria | NOT_STARTED |
| T515 | Race delete | SmartBlockCriteria | NOT_STARTED |
| T516 | Block without criteria | SmartBlockCriteria | NOT_STARTED |
| T517 | Invalid token 404 | SmartBlockCriteria | NOT_STARTED |
| T518 | BOLA LIST | Webstream | NOT_STARTED |
| T519 | __all__ exposure | Webstream | NOT_STARTED |
| T520 | SSRF internal URL | Webstream | NOT_STARTED |
| T521 | XSS MIME type | Webstream | NOT_STARTED |
| T522 | URL length | Webstream | NOT_STARTED |
| T523 | Invalid URL | Webstream | NOT_STARTED |
| T524 | 500 query params | Webstream | NOT_STARTED |
| T525 | XSS description | Webstream | NOT_STARTED |
| T526 | BOPLA owner | Webstream CREATE | NOT_STARTED |
| T527 | Unauthenticated create | Webstream | NOT_STARTED |
| T528 | BOPLA id | Webstream | NOT_STARTED |
| T529 | BOPLA timestamps | Webstream | NOT_STARTED |
| T530 | BOPLA extra fields | Webstream | NOT_STARTED |
| T531 | SSRF internal | Webstream | NOT_STARTED |
| T532 | SSRF metadata | Webstream | NOT_STARTED |
| T533 | Dangerous schemes | Webstream | NOT_STARTED |
| T534 | XSS name | Webstream | NOT_STARTED |
| T535 | XSS description | Webstream | NOT_STARTED |
| T536 | Name length | Webstream | NOT_STARTED |
| T537 | Empty name | Webstream | NOT_STARTED |
| T538 | Wrong Content-Type | Webstream | NOT_STARTED |
| T539 | Race condition | Webstream | NOT_STARTED |
| T540 | NOT NULL violation | Webstream | NOT_STARTED |
| T541 | BOLA UPDATE | Webstream | NOT_STARTED |
| T542 | BOLA DELETE | Webstream | NOT_STARTED |
| T543 | Error leak existence | Webstream | NOT_STARTED |
| T544 | SSRF UPDATE internal | Webstream | NOT_STARTED |
| T545 | SSRF UPDATE metadata | Webstream | NOT_STARTED |
| T546 | BOPLA owner | Webstream | NOT_STARTED |
| T547 | BOPLA id | Webstream | NOT_STARTED |
| T548 | BOPLA created_at | Webstream | NOT_STARTED |
| T549 | XSS name UPDATE | Webstream | NOT_STARTED |
| T550 | XSS description UPDATE | Webstream | NOT_STARTED |
| T551 | SSRF PUT | Webstream | NOT_STARTED |
| T552 | BOPLA owner PUT | Webstream | NOT_STARTED |
| T553 | Empty name UPDATE | Webstream | NOT_STARTED |
| T554 | Invalid URL UPDATE | Webstream | NOT_STARTED |
| T555 | Race UPDATE | Webstream | NOT_STARTED |
| T556 | DELETE status | Webstream | NOT_STARTED |
| T557 | Batch delete | Webstream | NOT_STARTED |
| T558 | Error leak | Webstream | NOT_STARTED |
| T559 | Race delete | Webstream | NOT_STARTED |
| T560 | Invalid token status | Webstream | NOT_STARTED |
| T561 | HTTP Method Override | Webstream | NOT_STARTED |
| T562 | BOLA UPDATE | Webstream | NOT_STARTED |
| T563 | BOLA DELETE | Webstream | NOT_STARTED |
| T564 | BOLA LIST | Webstream | NOT_STARTED |
| T567 | BOPLA owner | Webstream | NOT_STARTED |
| T568 | BOLA LIST | Schedule | NOT_STARTED |
| T569 | BOLA RETRIEVE | Schedule | NOT_STARTED |
| T573 | Error leak | Schedule | NOT_STARTED |
| T574 | Filter bypass | Schedule | NOT_STARTED |
| T575 | Invalid token 200 | Schedule | NOT_STARTED |
| T576 | BOLA CREATE | Schedule | NOT_STARTED |
| T577 | BOLA other file | Schedule | NOT_STARTED |
| T578 | BOLA other stream | Schedule | NOT_STARTED |
| T581 | No overlap validation | Schedule | NOT_STARTED |
| T582 | No time boundary | Schedule | NOT_STARTED |
| T583 | SSRF stream | Schedule | NOT_STARTED |
| T584 | Invalid token CREATE | Schedule | NOT_STARTED |
| T586 | Race CREATE | Schedule | NOT_STARTED |
| T587 | BOLA RETRIEVE | Schedule | NOT_STARTED |
| T589 | Invalid token 200 | Schedule | NOT_STARTED |
| T591 | Error leak RETRIEVE | Schedule | NOT_STARTED |
| T592 | BOLA UPDATE | Schedule | NOT_STARTED |
| T593 | BOLA other file | Schedule | NOT_STARTED |
| T594 | BOLA other stream | Schedule | NOT_STARTED |
| T595 | Overlap via UPDATE | Schedule | NOT_STARTED |
| T596 | SSRF UPDATE | Schedule | NOT_STARTED |
| T597 | Invalid token UPDATE | Schedule | NOT_STARTED |
| T598 | BOLA DELETE | Schedule | NOT_STARTED |
| T599 | Wrong DELETE status | Schedule | NOT_STARTED |
| T600 | Invalid token DELETE | Schedule | NOT_STARTED |
| T601 | Rate limiting DELETE | Schedule | NOT_STARTED |
| T602 | Error leak DELETE | Schedule | NOT_STARTED |
| T612 | Cross-instance | Schedule | NOT_STARTED |
| T613 | SQLi overbooked | Schedule | NOT_STARTED |
| T615 | overbooked bypass | Schedule | NOT_STARTED |
| T616 | BOLA overbooked | Schedule | NOT_STARTED |
| T617 | Host modify other | Schedule | NOT_STARTED |
| T618 | Host delete other | Schedule | NOT_STARTED |
| T619 | Change instance | Schedule | NOT_STARTED |
| T620 | Rate limiting LIST | PlayoutHistory | NOT_STARTED |
| T621 | BOPLA extra fields | PlayoutHistory | NOT_STARTED |
| T622 | BOLA other instance | PlayoutHistory | NOT_STARTED |
| T623 | Rate limiting CREATE | PlayoutHistory | NOT_STARTED |
| T624 | BOPLA UPDATE | PlayoutHistory | NOT_STARTED |
| T625 | BOPLA PATCH | PlayoutHistory | NOT_STARTED |
| T626 | BOLA metadata | PlayoutHistory | NOT_STARTED |
| T627 | BOPLA extra CREATE | Metadata | NOT_STARTED |
| T628 | BOPLA extra UPDATE | Metadata | NOT_STARTED |
| T629 | XSS key | Metadata | NOT_STARTED |
| T630 | XSS value | Metadata | NOT_STARTED |
| T631 | Rate limiting metadata | Metadata | NOT_STARTED |
| T632 | BOPLA extra Template | Template | NOT_STARTED |
| T633 | BOPLA extra UPDATE | Template | NOT_STARTED |
| T634 | BOPLA extra PATCH | Template | NOT_STARTED |
| T635 | XSS name | Template | NOT_STARTED |
| T636 | XSS type | Template | NOT_STARTED |
| T637 | Rate limiting CREATE | Template | NOT_STARTED |
| T638 | Rate limiting UPDATE | Template | NOT_STARTED |
| T639 | BOPLA extra CREATE | TemplateField | NOT_STARTED |
| T640 | BOPLA extra PATCH | TemplateField | NOT_STARTED |
| T641 | BOLA other template | TemplateField | NOT_STARTED |
| T642 | XSS name | TemplateField | NOT_STARTED |
| T643 | XSS label | TemplateField | NOT_STARTED |
| T644 | Negative position | TemplateField | NOT_STARTED |
| T645 | Rate limiting CREATE | TemplateField | NOT_STARTED |
| T646 | BOPLA extra CREATE | ListenerCount | NOT_STARTED |
| T647 | Count manipulation | ListenerCount | NOT_STARTED |
| T648 | Negative count | ListenerCount | NOT_STARTED |
| T649 | Rate limiting CREATE | ListenerCount | NOT_STARTED |
| T650 | Pagination missing | ListenerCount | NOT_STARTED |
| T651 | Future timestamp | ListenerCount | NOT_STARTED |
| T652 | End before start | ListenerCount | NOT_STARTED |
| T653 | BFLA guest | LiveLog | NOT_STARTED |
| T654 | BOPLA extra CREATE | LiveLog | NOT_STARTED |
| T655 | Fake end_time | LiveLog | NOT_STARTED |
| T656 | End before start | LiveLog | NOT_STARTED |
| T657 | Future start_time | LiveLog | NOT_STARTED |
| T658 | BOPLA extra PATCH | LiveLog | NOT_STARTED |
| T659 | XSS state | LiveLog | NOT_STARTED |
| T660 | Rate limiting CREATE | LiveLog | NOT_STARTED |
| T661 | Pagination missing | LiveLog | NOT_STARTED |
| T662 | Rate limiting UPDATE | LiveLog | NOT_STARTED |
| T663 | BOLA LIST | Podcast | NOT_STARTED |
| T664 | BFLA guest | Podcast | NOT_STARTED |
| T665 | ID format confusion | Podcast | NOT_STARTED |
| T673 | Owner ID exposure | Podcast | NOT_STARTED |
| T675 | Status code IDOR | Podcast | NOT_STARTED |
| T678 | Rate limiting LIST | Podcast | NOT_STARTED |
| T679 | Pagination missing | Podcast | NOT_STARTED |
| T682 | BOLA episodes | PodcastEpisode | NOT_STARTED |
| T703 | BOPLA extra CREATE | Podcast | NOT_STARTED |
| T706 | URL credentials | Podcast | NOT_STARTED |
| T708 | XSS title | Podcast | NOT_STARTED |
| T709 | XSS description | Podcast | NOT_STARTED |
| T710 | XSS itunes | Podcast | NOT_STARTED |
| T713 | Rate limiting CREATE | Podcast | NOT_STARTED |
| T721 | JavaScript URL | Podcast | NOT_STARTED |
| T722 | Race duplicate | Podcast | NOT_STARTED |
| T727 | BOLA RETRIEVE | Podcast | NOT_STARTED |
| T730 | BOPLA extra PATCH | Podcast | NOT_STARTED |
| T732 | XSS UPDATE title | Podcast | NOT_STARTED |
| T733 | XSS PATCH description | Podcast | NOT_STARTED |
| T735 | Rate limiting UPDATE | Podcast | NOT_STARTED |
| T736 | Rate limiting DELETE | Podcast | NOT_STARTED |
| T740 | Account lockout | Auth | NOT_STARTED |
| T741 | Weak passwords | User | NOT_STARTED |
| T742 | Common passwords | User | NOT_STARTED |
| T743 | Short passwords | User | NOT_STARTED |
| T745 | BFLA guest | Permissions | NOT_STARTED |
| T746 | Concurrent sessions | Settings | NOT_STARTED |
| T749 | Unicode crash | API Key | NOT_STARTED |
| T750 | Rate limiting API Key | API Key | NOT_STARTED |
| T751 | API Key format | API Key | NOT_STARTED |
| T752 | API Key length | API Key | NOT_STARTED |
| T753 | Case sensitivity | Auth | NOT_STARTED |
| T755 | Token expiration | API Key | NOT_STARTED |
| T756 | Token scope | API Key | NOT_STARTED |
| T769 | Rate limiting public | Public endpoints | NOT_STARTED |
| T783 | Brute force password | Auth | NOT_STARTED |
| T784 | Brute force API Key | API Key | NOT_STARTED |
| T793 | Unicode unhandled | Auth | NOT_STARTED |
| T806 | BOLA RETRIEVE | Playlist | NOT_STARTED |
| T807 | BOLA LIST | Playlist | NOT_STARTED |
| T808 | BOLA UPDATE | Playlist | NOT_STARTED |
| T809 | BOLA DELETE | Playlist | NOT_STARTED |
| T810 | BOPLA id | Playlist | NOT_STARTED |
| T811 | BOPLA created_at | Playlist | NOT_STARTED |
| T812 | BOPLA owner | Playlist | NOT_STARTED |
| T813 | BOPLA extra | Playlist | NOT_STARTED |
| T814 | SQLi length | Playlist | NOT_STARTED |
| T817 | Invalid time format | Playlist | NOT_STARTED |
| T818 | Overflow length | Playlist | NOT_STARTED |
| T823 | Rate limiting CREATE | Playlist | NOT_STARTED |
| T829 | BOLA RETRIEVE | SmartBlock | NOT_STARTED |
| T830 | BOLA LIST | SmartBlock | NOT_STARTED |
| T831 | BOLA UPDATE | SmartBlock | NOT_STARTED |
| T832 | BOLA DELETE | SmartBlock | NOT_STARTED |
| T833 | BOPLA id | SmartBlock | NOT_STARTED |
| T834 | BOPLA created_at | SmartBlock | NOT_STARTED |
| T835 | BOPLA owner | SmartBlock | NOT_STARTED |
| T836 | BOPLA extra | SmartBlock | NOT_STARTED |
| T837 | Invalid kind | SmartBlock | NOT_STARTED |
| T849 | Error leak structure | SmartBlock | NOT_STARTED |
| T850 | BOLA RETRIEVE | File | NOT_STARTED |
| T851 | BOLA LIST | File | NOT_STARTED |
| T853 | BOLA DELETE | File | NOT_STARTED |
| T854 | BOLA download | File | NOT_STARTED |
| T855 | Path traversal | File | NOT_STARTED |
| T856 | Path traversal UPDATE | File | NOT_STARTED |
| T857 | Absolute path | File | NOT_STARTED |
| T858 | BOPLA id | File | NOT_STARTED |
| T859 | BOPLA created_at | File | NOT_STARTED |
| T860 | BOPLA owner | File | NOT_STARTED |
| T861 | BOPLA extra | File | NOT_STARTED |
| T862 | Rate limiting CREATE | File | NOT_STARTED |
| T863 | BOLA cascade delete | Show | NOT_STARTED |
| T864 | BOLA cascade delete | Playlist | NOT_STARTED |
| T869 | Rate limiting delete | Schedule | NOT_STARTED |
| T873 | FK constraint 500 | Library | NOT_STARTED |
| T912 | Header injection \\n | API Key | NOT_STARTED |
| T913 | Header injection \\r | API Key | NOT_STARTED |
| T914 | Fixture bug | conftest.py | NOT_STARTED |
| T915 | Hardcoded password | Settings | NOT_STARTED |
| T916 | Short API key | Settings | NOT_STARTED |
| T917 | Short SECRET_KEY | Settings | NOT_STARTED |
| T918 | CSRF HttpOnly | Settings | NOT_STARTED |

---

## Рекомендуемый порядок фиксов

### Этап 1: CRITICAL Auth & BOLA
- T354, T378, T382, T384, T387 — Anonymous access
- T575, T584, T589, T597, T600 — Invalid token bypass
- T806-T809, T829-T832, T850-T854 — BOLA CRUD
- T912, T913 — Header injection

### Этап 2: CRITICAL Mass Assignment
- T810-T812, T833-T835, T858-T860 — Owner/id/timestamp writable
- T887, T891, T905 — Workflow bypass

### Этап 3: HIGH XSS & SSRF
- T402, T708-T710 — Stored XSS
- T520, T523, T531-T532, T544-T545 — SSRF

### Этап 4: HIGH Rate Limiting
- T20, T424, T601, T620-T623 — Core endpoints
- T678, T713, T735-T736 — Podcast

### Этап 5: MEDIUM Validation & Business Logic
- T481, T500, T648, T644 — Negative values
- T855-T857, T886-T890 — Path traversal
- T581, T582, T595 — Schedule logic

---

## Примечания

- Всего задач в файле: ~6778 строк
- Активных (NOT_STARTED): ~275+
- Открытых багов (OPEN): ~20
- CRITICAL приоритет: ~85 задач
- HIGH приоритет: ~75 задач
- MEDIUM приоритет: ~90 задач
- LOW приоритет: ~25 задач
