# LibreTime Legacy — План покрытия тестами

> **Цель**: 100% покрытие критических путей  
> **Подход**: Итеративный, атомарный, приоритетный  
> **Фреймворк**: PHPUnit 5.7 (без обновлений)  
> **Среда**: Docker (./test.sh)

---

## Фаза 0: Foundation (Недели 1-2)
> Инфраструктура и критические зависимости

### Задача 0.1: Фикс путей в тестовой инфраструктуре
- [ ] 0.1.1 Исправить `PreferenceUnitTest.php` — заменить `../application/configs/conf.php` на `CONFIG_PATH`
- [ ] 0.1.2 Проверить все `require_once` в tests/ на использование относительных путей
- [ ] 0.1.3 Создать `TestBootstrap.php` — единая точка входа для всех тестов
- [ ] 0.1.4 Убедиться что `phpunit.xml` корректно загружает bootstrap

### Задача 0.2: Test Helpers Coverage
- [ ] 0.2.1 Протестировать `TestHelper::getDbZendConfig()` — валидность конфига
- [ ] 0.2.2 Протестировать `TestHelper::installTestDatabase()` — создание БД
- [ ] 0.2.3 Протестировать `AirtimeInstall::CreateDatabaseTables()` — SQL миграции
- [ ] 0.2.4 Создать фабрику тестовых данных `ModelFactory`

### Задача 0.3: Fixtures и Test Data
- [ ] 0.3.1 Создать YAML-фикстуры для базовых сущностей (User, Show, File)
- [ ] 0.3.2 Создать `testdata/ShowData.php` — фабрика тестовых шоу
- [ ] 0.3.3 Создать `testdata/FileData.php` — фабрика тестовых файлов
- [ ] 0.3.4 Создать `testdata/PlaylistData.php` — фабрика плейлистов

---

## Фаза 1: Common Helpers (Недели 2-3)
> Pure functions — легко тестировать, высокая ценность

### Задача 1.1: DateHelper
- [ ] 1.1.1 Тест `DateHelper::getUTCDateTime()` — валидные/невалидные даты
- [ ] 1.1.2 Тест `DateHelper::getLocalDateTime()` — timezone conversion
- [ ] 1.1.3 Тест `DateHelper::getTimeInterval()` — интервалы
- [ ] 1.1.4 Тест `DateHelper::isInPast()` — граничные случаи
- [ ] 1.1.5 Тест `DateHelper::getDateRange()` — диапазоны

### Задача 1.2: FileDataHelper
- [ ] 1.2.1 Тест `FileDataHelper::createFileFromUpload()` — валидный файл
- [ ] 1.2.2 Тест `FileDataHelper::parseMetadata()` — извлечение метаданных
- [ ] 1.2.3 Тест `FileDataHelper::validateFileExtension()` — валидация
- [ ] 1.2.4 Тест `FileDataHelper::sanitizeFilename()` — санитизация
- [ ] 1.2.5 Тест `FileDataHelper::getMimeType()` — определение типов

### Задача 1.3: HTTPHelper
- [ ] 1.3.1 Тест `HTTPHelper::getClientIp()` — IP из headers
- [ ] 1.3.2 Тест `HTTPHelper::isAjaxRequest()` — XHR detection
- [ ] 1.3.3 Тест `HTTPHelper::buildUrl()` — построение URL

### Задача 1.4: SecurityHelper
- [ ] 1.4.1 Тест `SecurityHelper::generateToken()` — токены
- [ ] 1.4.2 Тест `SecurityHelper::hashPassword()` — хеширование
- [ ] 1.4.3 Тест `SecurityHelper::verifyCsrfToken()` — CSRF защита
- [ ] 1.4.4 Тест `SecurityHelper::sanitizeInput()` — XSS защита

### Задача 1.5: LocaleHelper
- [ ] 1.5.1 Тест `LocaleHelper::getAvailableLocales()` — список локалей
- [ ] 1.5.2 Тест `LocaleHelper::normalizeLanguageCode()` — нормализация
- [ ] 1.5.3 Тест `LocaleHelper::getDateFormat()` — форматы дат

### Задача 1.6: OsPath
- [ ] 1.6.1 Тест `OsPath::join()` — объединение путей
- [ ] 1.6.2 Тест `OsPath::normalize()` — нормализация
- [ ] 1.6.3 Тест `OsPath::isAbsolute()` — проверка абсолютных путей

### Задача 1.7: Timezone
- [ ] 1.7.1 Тест `Timezone::getUserTimezone()` — timezone пользователя
- [ ] 1.7.2 Тест `Timezone::convertToUTC()` — конверсия
- [ ] 1.7.3 Тест `Timezone::getTimezoneList()` — список

---

## Фаза 2: Service Layer — Core (Недели 3-5)
> Критическая бизнес-логика, относительно изолирована

### Задача 2.1: ShowService — Create Operations
- [ ] 2.1.1 Тест `addUpdateShow()` — создание шоу без повторов
- [ ] 2.1.2 Тест `addUpdateShow()` — создание weekly repeat
- [ ] 2.1.3 Тест `addUpdateShow()` — создание bi-weekly repeat
- [ ] 2.1.4 Тест `addUpdateShow()` — создание monthly repeat
- [ ] 2.1.5 Тест `addUpdateShow()` — шоу с rebroadcast
- [ ] 2.1.6 Тест `addUpdateShow()` — шоу с recording

### Задача 2.2: ShowService — Update Operations
- [ ] 2.2.1 Тест редактирования шоу без изменения repeat
- [ ] 2.2.2 Тест изменения repeat type (weekly → bi-weekly)
- [ ] 2.2.3 Тест изменения времени шоу
- [ ] 2.2.4 Тест удаления repeat (weekly → no repeat)
- [ ] 2.2.5 Тест добавления repeat days
- [ ] 2.2.6 Тест удаления repeat days

### Задача 2.3: ShowService — Delete Operations
- [ ] 2.3.1 Тест удаления single instance
- [ ] 2.3.2 Тест удаления current and following
- [ ] 2.3.3 Тест удаления всего шоу
- [ ] 2.3.4 Тест удаления linked show

### Задача 2.4: ShowService — Query Operations
- [ ] 2.4.1 Тест `getFutureShowInstances()`
- [ ] 2.4.2 Тест `getShowLength()`
- [ ] 2.4.3 Тест `formatShowDuration()`
- [ ] 2.4.4 Тест `calculateEndDate()`

### Задача 2.5: ShowService — Private Methods (через Reflection)
- [ ] 2.5.1 Тест `createUTCStartEndDateTime()`
- [ ] 2.5.2 Тест `getNextMonthlyWeeklyRepeatDate()`
- [ ] 2.5.3 Тест `getNextMonthlyMonthlyRepeatDate()`
- [ ] 2.5.4 Тест `getMonthlyWeeklyRepeatInterval()`

### Задача 2.6: SchedulerService
- [ ] 2.6.1 Тест `scheduleAfter()` — scheduling после шоу
- [ ] 2.6.2 Тест `removeGaps()` — удаление gap'ов
- [ ] 2.6.3 Тест `reschedule()` — перепланирование
- [ ] 2.6.4 Тест `isScheduleEmpty()` — проверка пустоты
- [ ] 2.6.5 Тест `getShowContent()` — получение контента

### Задача 2.7: UserService
- [ ] 2.7.1 Тест `createUser()` — создание пользователя
- [ ] 2.7.2 Тест `updateUser()` — обновление
- [ ] 2.7.3 Тест `deleteUser()` — удаление
- [ ] 2.7.4 Тест `getUserByLogin()` — поиск
- [ ] 2.7.5 Тест `changePassword()` — смена пароля
- [ ] 2.7.6 Тест `validateUserType()` — типы пользователей

### Задача 2.8: MediaService
- [ ] 2.8.1 Тест `uploadFile()` — загрузка
- [ ] 2.8.2 Тест `updateMetadata()` — обновление метаданных
- [ ] 2.8.3 Тест `deleteFile()` — удаление
- [ ] 2.8.4 Тест `moveFile()` — перемещение
- [ ] 2.8.5 Тест `searchFiles()` — поиск

### Задача 2.9: PodcastService
- [ ] 2.9.1 Тест `importPodcast()` — импорт RSS
- [ ] 2.9.2 Тест `updatePodcast()` — обновление
- [ ] 2.9.3 Тест `deletePodcast()` — удаление
- [ ] 2.9.4 Тест `syncEpisodes()` — синхронизация эпизодов

---

## Фаза 3: Models — Core (Недели 5-7)
> Требуют БД, интеграционные тесты

### Задача 3.1: Show Model
- [ ] 3.1.1 Тест `getName()`, `setName()`
- [ ] 3.1.2 Тест `getDescription()`, `setDescription()`
- [ ] 3.1.3 Тест `getColor()`, `setColor()`
- [ ] 3.1.4 Тест `getHosts()` — получение ведущих
- [ ] 3.1.5 Тест `addHost()`, `removeHost()`
- [ ] 3.1.6 Тест `isRecorded()` — флаг записи

### Задача 3.2: ShowInstance Model
- [ ] 3.2.1 Тест `getShow()` — связь с шоу
- [ ] 3.2.2 Тест `getStartDateTime()`, `getEndDateTime()`
- [ ] 3.2.3 Тест `isRecorded()` — статус записи
- [ ] 3.2.4 Тест `addFileToShow()` — добавление файла
- [ ] 3.2.5 Тест `clearShow()` — очистка

### Задача 3.3: Schedule Model
- [ ] 3.3.1 Тест `IsFileScheduledInTheFuture()`
- [ ] 3.3.2 Тест `checkOverlappingShows()` — проверка пересечений
- [ ] 3.3.3 Тест `getRangeScheduled()` — диапазон
- [ ] 3.3.4 Тест `getShowList()` — список шоу

### Задача 3.4: Block Model (Smart Blocks)
- [ ] 3.4.1 Тест `saveSmartBlockCriteria()` — сохранение критериев
- [ ] 3.4.2 Тест `getListOfFilesUnderLimit()` — получение файлов
- [ ] 3.4.3 Тест `getLength()` — длительность
- [ ] 3.4.4 Тест `update()`,`delete()` — CRUD

### Задача 3.5: Playlist Model
- [ ] 3.5.1 Тест `create()` — создание
- [ ] 3.5.2 Тест `addContent()` — добавление контента
- [ ] 3.5.3 Тест `moveItem()` — перемещение
- [ ] 3.5.4 Тест `deleteItem()` — удаление элемента
- [ ] 3.5.5 Тест `getLength()` — длительность

### Задача 3.6: StoredFile Model
- [ ] 3.6.1 Тест `create()` — создание
- [ ] 3.6.2 Тест `updateMetadata()` — обновление метаданных
- [ ] 3.6.3 Тест `delete()` — удаление
- [ ] 3.6.4 Тест `getMetadata()` — получение метаданных

### Задача 3.7: User Model
- [ ] 3.7.1 Тест `create()` — создание
- [ ] 3.7.2 Тест `setPassword()` — установка пароля
- [ ] 3.7.3 Тест `checkPassword()` — проверка
- [ ] 3.7.4 Тест `getType()` — тип пользователя
- [ ] 3.7.5 Тест `isAdmin()` — проверка прав

### Задача 3.8: Preference Model
- [ ] 3.8.1 Тест `SetValue()` / `GetValue()`
- [ ] 3.8.2 Тест `SetShowsPopulatedUntil()`
- [ ] 3.8.3 Тест `GetShowsPopulatedUntil()`
- [ ] 3.8.4 Тест `GetStationName()`
- [ ] 3.8.5 Тест `GetDefaultTimezone()`

### Задача 3.9: Library Model
- [ ] 3.9.1 Тест `getFiles()` — получение файлов
- [ ] 3.9.2 Тест `search()` — поиск
- [ ] 3.9.3 Тест `getFileCount()` — подсчёт

### Задача 3.10: Webstream Model
- [ ] 3.10.1 Тест `create()` — создание веб-стрима
- [ ] 3.10.2 Тест `getUrl()` — получение URL
- [ ] 3.10.3 Тест `setMetadata()` — метаданные

---

## Фаза 4: Forms (Недели 7-8)
> Валидация данных

### Задача 4.1: Login Form
- [ ] 4.1.1 Тест валидации username
- [ ] 4.1.2 Тест валидации password
- [ ] 4.1.3 Тест CSRF токена

### Задача 4.2: AddUser Form
- [ ] 4.2.1 Тест валидации email
- [ ] 4.2.2 Тест валидации username (уникальность)
- [ ] 4.2.3 Тест валидации password (сложность)
- [ ] 4.2.4 Тест валидации user type

### Задача 4.3: AddShow Forms
- [ ] 4.3.1 Тест `AddShowWhat` — название, описание
- [ ] 4.3.2 Тест `AddShowWhen` — дата/время
- [ ] 4.3.3 Тест `AddShowRepeats` — repeat type
- [ ] 4.3.4 Тест `AddShowWho` — hosts
- [ ] 4.3.5 Тест `AddShowStyle` — цвет, настройки

### Задача 4.4: EditUser Form
- [ ] 4.4.1 Тест редактирования профиля
- [ ] 4.4.2 Тест смены пароля
- [ ] 4.4.3 Тест изменения прав

### Задача 4.5: Preferences Forms
- [ ] 4.5.1 Тест `GeneralPreferences`
- [ ] 4.5.2 Тест `LiveStreamingPreferences`
- [ ] 4.5.3 Тест `StreamSetting`

---

## Фаза 5: Auth & Security (Недели 8-9)
> Аутентификация и авторизация

### Задача 5.1: Auth Model
- [ ] 5.1.1 Тест `getAuthAdapter()` — адаптер
- [ ] 5.1.2 Тест `authenticate()` — успешная аутентификация
- [ ] 5.1.3 Тест `authenticate()` — неудачная (wrong password)
- [ ] 5.1.4 Тест `authenticate()` — неудачная (user not found)
- [ ] 5.1.5 Тест `logout()` — выход

### Задача 5.2: ACL Plugin
- [ ] 5.2.1 Тест доступа для guest
- [ ] 5.2.2 Тест доступа для host
- [ ] 5.2.3 Тест доступа для admin
- [ ] 5.2.4 Тест доступа для superadmin
- [ ] 5.2.5 Тест запрета доступа (403)

### Задача 5.3: Custom Validators
- [ ] 5.3.1 Тест `UserNameValidate`
- [ ] 5.3.2 Тест `NotDemoValidate`
- [ ] 5.3.3 Тест `ConditionalNotEmpty`

---

## Фаза 6: Controllers — Core (Недели 9-11)
> Интеграционные тесты контроллеров

### Задача 6.1: LoginController
- [ ] 6.1.1 Тест `indexAction()` — отображение формы
- [ ] 6.1.2 Тест `indexAction()` — успешный логин
- [ ] 6.1.3 Тест `indexAction()` — неудачный логин
- [ ] 6.1.4 Тест `logoutAction()`
- [ ] 6.1.5 Тест `passwordChangeAction()`

### Задача 6.2: UserController
- [ ] 6.2.1 Тест `indexAction()` — список пользователей
- [ ] 6.2.2 Тест `addUserAction()` — создание
- [ ] 6.2.3 Тест `editUserAction()` — редактирование
- [ ] 6.2.4 Тест `removeUserAction()` — удаление
- [ ] 6.2.5 Тест `getUserDataAction()` — AJAX

### Задача 6.3: ScheduleController
- [ ] 6.3.1 Тест `indexAction()` — отображение календаря
- [ ] 6.3.2 Тест `addShowAction()` — создание
- [ ] 6.3.3 Тест `editShowAction()` — редактирование
- [ ] 6.3.4 Тест `deleteShowAction()` — удаление
- [ ] 6.3.5 Тест `cancelShowAction()` — отмена
- [ ] 6.3.6 Тест `eventFeedAction()` — JSON feed

### Задача 6.4: PlaylistController
- [ ] 6.4.1 Тест `indexAction()`
- [ ] 6.4.2 Тест `newAction()` — создание
- [ ] 6.4.3 Тест `editAction()` — редактирование
- [ ] 6.4.4 Тест `deleteAction()` — удаление
- [ ] 6.4.5 Тест `addItemAction()` — AJAX добавление

### Задача 6.5: LibraryController
- [ ] 6.5.1 Тест `indexAction()`
- [ ] 6.5.2 Тест `uploadAction()` — загрузка
- [ ] 6.5.3 Тест `editFileMdAction()` — метаданные
- [ ] 6.5.4 Тест `deleteAction()` — удаление
- [ ] 6.5.5 Тест `getFileMetadataAction()` — AJAX

### Задача 6.6: ApiController
- [ ] 6.6.1 Тест `dispatchMetadata()` — API endpoint
- [ ] 6.6.2 Тест `listAllFiles()` — список файлов
- [ ] 6.6.3 Тест `status()` — статус системы

---

## Фаза 7: Integration & Edge Cases (Недели 11-12)
> Сквозные сценарии

### Задача 7.1: Full Show Lifecycle
- [ ] 7.1.1 Тест: Создать шоу → Добавить контент → Запустить → Завершить
- [ ] 7.1.2 Тест: Создать повторяющееся шоу → Редактировать один instance
- [ ] 7.1.3 Тест: Запись шоу → Проверить запись в истории

### Задача 7.2: File Upload Flow
- [ ] 7.2.1 Тест: Upload → Metadata extraction → Добавление в плейлист
- [ ] 7.2.2 Тест: Upload invalid file → Error handling

### Задача 7.3: Scheduling Conflicts
- [ ] 7.3.1 Тест: Попытка создать overlapping shows
- [ ] 7.3.2 Тест: Reschedule с конфликтом

### Задача 7.4: Timezone Edge Cases
- [ ] 7.4.1 Тест: DST transition (summer time)
- [ ] 7.4.2 Тест: Cross-timezone scheduling
- [ ] 7.4.3 Тест: Negative timezone offsets

### Задача 7.5: Permission Scenarios
- [ ] 7.5.1 Тест: Host пытается редактировать чужое шоу
- [ ] 7.5.2 Тест: Guest пытается создать шоу
- [ ] 7.5.3 Тест: Program Manager права

---

## Фаза 8: REST API Module (Недели 12-13)
> application/modules/rest/

### Задача 8.1: MediaController (REST)
- [ ] 8.1.1 Тест GET /media — список
- [ ] 8.1.2 Тест GET /media/:id — детали
- [ ] 8.1.3 Тест POST /media — создание
- [ ] 8.1.4 Тест PUT /media/:id — обновление
- [ ] 8.1.5 Тест DELETE /media/:id — удаление

### Задача 8.2: PodcastController (REST)
- [ ] 8.2.1 Тест GET /podcasts
- [ ] 8.2.2 Тест POST /podcasts
- [ ] 8.2.3 Тест PUT /podcasts/:id
- [ ] 8.2.4 Тест DELETE /podcasts/:id

### Задача 8.3: ShowImageController
- [ ] 8.3.1 Тест GET изображения шоу
- [ ] 8.3.2 Тест POST загрузки

---

## Фаза 9: Formatters & Utilities (Недели 13-14)
> application/models/formatters/

### Задача 9.1: Formatters
- [ ] 9.1.1 Тест `LengthFormatter` — форматирование длительности
- [ ] 9.1.2 Тест `BitrateFormatter` — битрейт
- [ ] 9.1.3 Тест `SamplerateFormatter` — sample rate
- [ ] 9.1.4 Тест `TimeFilledFormatter` — заполненное время

---

## Фаза 10: Final Coverage & Polish (Недели 14-15)

### Задача 10.1: Coverage Analysis
- [ ] 10.1.1 Запустить coverage report
- [ ] 10.1.2 Выявить непокрытые участки
- [ ] 10.1.3 Дописать тесты для gap'ов

### Задача 10.2: Performance Tests
- [ ] 10.2.1 Тест больших плейлистов (>1000 items)
- [ ] 10.2.2 Тест большого количества повторяющихся шоу
- [ ] 10.2.3 Тест поиска по библиотеке (stress)

### Задача 10.3: Documentation
- [ ] 10.3.1 Документировать все test helpers
- [ ] 10.3.2 Создать HOWTO для добавления новых тестов
- [ ] 10.3.3 Обновить TESTING.md с результатами

---

## Приоритеты по критичности

### Critical (Падение = остановка вещания)
1. ShowService — создание/редактирование шоу
2. Schedule — планирование
3. Playout — воспроизведение

### High (Падение = деградация функциональности)
4. UserService — управление пользователями
5. MediaService — работа с файлами
6. Auth — аутентификация

### Medium (Падение = неудобства)
7. PodcastService
8. Forms validation
9. Controllers

### Low (Падение = косметические проблемы)
10. Helpers
11. Formatters
12. Widgets

---

## Метрики успеха

| Фаза | Целевое покрытие | Реальное | Статус |
|------|------------------|----------|--------|
| Foundation | 90% | TBD | 🔄 |
| Common Helpers | 90% | TBD | 🔄 |
| Service Layer | 85% | TBD | 🔄 |
| Models | 80% | TBD | 🔄 |
| Forms | 75% | TBD | 🔄 |
| Controllers | 70% | TBD | 🔄 |
| REST API | 80% | TBD | 🔄 |
| **TOTAL** | **80%** | **<5%** | 🚀 |

---

## Конвенции для тестов

```php
// Именование
class ShowServiceTest extends PHPUnit_Framework_TestCase

// Структура теста
public function test<MethodName>_<Condition>_<ExpectedResult>()
// Пример: testAddUpdateShow_WeeklyRepeat_CreatesInstances()

// Комментарий к тесту
/**
 * @test
 * Given: Show data with weekly repeat
 * When: addUpdateShow() called
 * Then: Creates 4 instances for next month
 */

// Использование фикстур
$this->givenUser('admin');
$this->givenShow(['name' => 'Test Show', 'repeat_type' => 'weekly']);
```

---

*План создан: 2026-04-07*  
*Всего задач: ~120*  
*Оценка времени: 15 недель (1 разработчик)*  
*Рекомендуемый темп: 8-10 задач/неделя*
