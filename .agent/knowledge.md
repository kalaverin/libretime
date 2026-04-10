---
# Machine Index
version: 1
schema: knowledge-graph
last_updated: 2026-04-07T13:16:18Z
graph_hash: ""
---

<!-- Protocol: ~/.config/kimi/skills/knowledge-protocol/SKILL.md (modified: 2026-04-07T12:03:05Z, commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7) -->
<!-- The following section is a FULL COPY of ~/.config/kimi/skills/knowledge-protocol/SKILL.md
     Protocol commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7
     Protocol modified: 2026-04-07T12:03:05Z -->
---
name: knowledge-protocol
description: Protocol for maintaining codebase knowledge — via MCP MemPalace (preferred) OR .agent/knowledge.md (fallback)
---

# Knowledge Protocol

Accumulated codebase knowledge for AI agents. **Primary storage:** MCP MemPalace server. **Fallback:** `.agent/knowledge.md` when MCP unavailable.

## File Structure

```
repo-root/
├── mempalace.yaml          # Optional: wing/room taxonomy
└── .agent/
    └── knowledge.md        # Fallback when MCP unavailable
```

## Storage Selection Priority

| Priority | Storage | Condition |
|----------|---------|-----------|
| 1 | **MCP MemPalace** | MCP `mempalace` server available |
| 2 | **CLI MemPalace** | MCP unavailable BUT `mempalace.yaml` exists → use `mempalace` CLI |
| 3 | **Local file** | No MCP and no `mempalace.yaml` → use `.agent/knowledge.md` |

**Never split knowledge** — use exactly one storage system per session.

## Read on Session Start

### Step 1: Attempt MCP Mode
1. **Call `mempalace_status`**:
   - **Success**: MCP mode activated
   - **Failure**: Go to Step 2 (File Mode)
2. If `.agent/knowledge.md` has content:
   - **Migrate** to MCP: for each YAML block, call `mempalace_add_drawer`
   - Truncate file to stub after successful migration
3. Acknowledge: "Knowledge: MCP active, migrated X entries"

### Step 2: CLI Mode (MCP unavailable, mempalace.yaml exists)
1. Check if `mempalace.yaml` exists in repo root:
   - **Yes**: CLI mode activated
   - **No**: Go to Step 3 (File Mode)
2. **On session start**: Shell `mempalace wake-up [--wing <wing>]` → inject context
3. **For search**: Shell `mempalace search "query"`
4. Acknowledge: "Knowledge: CLI mode (mempalace.yaml), wing: X"

### Step 3: File Mode (MCP unavailable, no mempalace.yaml)
1. Read `.agent/knowledge.md` entirely
2. Parse YAML blocks — restore mental model
3. Acknowledge: "Knowledge: file mode, loaded X components, Y gotchas"

## Write Triggers (MANDATORY)

### MCP Mode (when `mempalace_status` succeeded)

| Trigger | Command |
|---------|---------|
| Component discovered | `mempalace_kg_add` + `mempalace_add_drawer(room="components")` |
| Gotcha found | `mempalace_add_drawer(room="gotchas")` |
| Insight discovered | `mempalace_add_drawer(room="insights")` |
| Investigation concluded | `mempalace_add_drawer(room="investigations")` |
| Data flow traced | `mempalace_add_drawer(room="architecture")` |

### CLI Mode (mempalace.yaml exists, MCP unavailable)
Read-only mode via CLI:
- **Search**: `mempalace search "query" [--wing WING] [--room ROOM]`
- **Wake-up**: `mempalace wake-up [--wing WING]` (on session start)

Writes go to `.agent/knowledge.md` (file mode) until MCP available.

### File Mode (no mempalace.yaml, MCP unavailable)
Use traditional YAML block updates in `.agent/knowledge.md`.

## Migration Procedure

**From file to MCP (one-time):**

```yaml
migration_steps:
  1_verify: "Call mempalace_status to confirm MCP availability"
  2_cli_check: "If MCP unavailable, check for mempalace.yaml → use CLI mode"
  3_read: "Read .agent/knowledge.md entirely"
  4_migrate:
    - For each YAML block → mempalace_add_drawer(wing=..., room=..., content=...)
    - For relationships → mempalace_kg_add(subject=..., predicate=..., object=...)
  5_cleanup: "Truncate knowledge.md to stub"
  6_verify: "Call mempalace_search to confirm migration"
```

## File Mode Schema (YAML)

**Only when MCP unavailable:**

```yaml
dependency_graph:
  components:
    component_name:
      type: [service|repository|router|model|utility]
      path: file_path
      depends_on: [list_of_components]
      provides: [list_of_capabilities]
      critical: true|false

class_hierarchy:
  classes:
    ClassName:
      extends: ParentClass
      mixins: [Mixin1, Mixin2]
      implements: [Interface1]
      abstract: true|false
      file: path/to/file.py

gotchas:
  - id: unique_id
    severity: [critical|high|medium|low]
    category: [behavior|performance|security|environment]
    title: "Short description"
    description: "Detailed explanation"
    location: "Where it occurs"
    discovered: "YYYY-MM-DDTHH:mm:ssZ"

insights:
  - id: insight_001
    type: [pattern|connection|performance|security|design]
    title: "Brief description"
    description: "Detailed insight"
    confidence: [confirmed|likely|speculative]
    discovered: "YYYY-MM-DDTHH:mm:ssZ"

investigation_log:
  - id: INV-001
    topic: "What was investigated"
    status: [ongoing|resolved|stalled]
    conclusion: "What was learned"
    discovered: "YYYY-MM-DDTHH:mm:ssZ"
    resolved: "YYYY-MM-DDTHH:mm:ssZ"
```

## Save Work / Persist State

### MCP Mode
1. All knowledge already persisted via MCP calls
2. Ensure `mempalace_diary_write` called if session ending
3. No local file operations

### CLI Mode (mempalace.yaml exists, MCP unavailable)
1. No persistent writes to palace via CLI (read-only)
2. Accumulate new knowledge to `.agent/knowledge.md` (file mode)
3. Flush pending knowledge to YAML blocks

### File Mode (no mempalace.yaml)
1. Flush pending knowledge to `.agent/knowledge.md` YAML blocks
2. Verify file written

## Cross-References

- **mempalace-protocol**: MCP server commands, AAAK format
- **memory-protocol**: Session history (always local file)
- **decision-protocol**: Architectural decisions
- **task-protocol**: Work tracking

## Implementation Notes

1. **Check MCP availability** each session via `mempalace_status`
2. **Graceful fallback** — MCP failure → automatically switch to file mode
3. **No caching** — check MCP availability each session
<!-- END OF PROTOCOL COPY -->

# LEGACY PHP PROJECT — COMPLETE TESTING PREREQUISITES

> **Status**: FROZEN — PHP 7.4 only, no updates allowed  
> **Scope**: Unit testing, bug detection, bug fixing (no refactoring)  
> **Generated**: 2026-04-07T13:16:18Z

---

## 1. PROJECT OVERVIEW

```yaml
legacy_project:
  path: legacy/
  language: PHP 7.4 (FROZEN — no 8.x migration)
  framework: Zend Framework 1 (zf1s fork v1.13)
  orm: Propel 1.6 (libretime fork, dev-main)
  lines_of_code: ~45,000 PHP (excluding generated Propel models)
  architecture: MVC with REST API module
  status: Maintenance mode only
```

---

## 2. REQUIRED BINARIES IN PATH

### Core Runtime
| Binary | Version | Purpose |
|--------|---------|---------|
| `php` | 7.4.x (exact) | PHP interpreter |
| `php-fpm` | 7.4.x | FastCGI for integration tests |
| `composer` | ^2.0 | Dependency management |
| `psql` | 12+ | PostgreSQL client |
| `pg_config` | — | PHP extension compilation |

### Project Tools (via composer)
| Binary | Version | Purpose |
|--------|---------|---------|
| `vendor/bin/phpunit` | 5.7 (locked) | Unit testing framework |
| `vendor/bin/propel-gen` | 1.6 | ORM model generator |

---

## 3. REQUIRED PHP EXTENSIONS

### Mandatory for Application
```
pdo_pgsql    - PostgreSQL PDO driver
pgsql        - PostgreSQL procedural interface
mbstring     - Multi-byte string handling
json         - JSON encoding/decoding
xml          - XML processing
ctype        - Character type checking
tokenizer    - PHP tokenization
session      - Session handling
curl         - HTTP requests
fileinfo     - File type detection
exif         - Metadata extraction
```

### For Testing & Coverage
```
xdebug v2.9.x  - Code coverage (recommended for accuracy)
# OR
pcov           - Alternative coverage driver (faster)
```

---

## 4. DEPENDENCY VERSIONS (LOCKED)

### Production Dependencies (composer.json)
```yaml
php: "^7.4"
adbario/php-dot-notation: "^3.0.0"
composer/semver: "^3.2"
james-heinrich/getid3: "^1.9"
league/uri: "^6.7"
libretime/celery-php: "dev-main" (fork)
libretime/propel1: "dev-main" (fork)
php-amqplib/php-amqplib: "^3.0"
simplepie/simplepie: "^1.5"
symfony/config: "^5.4"
zf1s/zend-acl: "^1.13"
zf1s/zend-application: "^1.13"
zf1s/zend-auth: "^1.13"
zf1s/zend-cache: "^1.13"
zf1s/zend-controller: "^1.13"
zf1s/zend-date: "^1.13"
zf1s/zend-db: "^1.13"
zf1s/zend-file: "^1.13"
zf1s/zend-file-transfer: "^1.13"
zf1s/zend-filter: "^1.13"
zf1s/zend-form: "^1.13"
zf1s/zend-http: "^1.13"
zf1s/zend-json: "^1.13"
zf1s/zend-layout: "^1.13"
zf1s/zend-loader: "^1.13"
zf1s/zend-log: "^1.13"
zf1s/zend-navigation: "^1.13"
zf1s/zend-rest: "^1.13"
zf1s/zend-session: "^1.13"
zf1s/zend-validate: "^1.13"
zf1s/zend-version: "^1.13"
zf1s/zend-view: "^1.13"
```

### Development Dependencies
```yaml
phpunit/dbunit: "^2.0"
phpunit/phpunit: "^5.7" (DEPRECATED, locked — migration breaks compatibility)
zf1s/zend-test: "^1.13"
```

---

## 5. PROJECT STRUCTURE

```
legacy/
├── application/
│   ├── Bootstrap.php              # Application bootstrap
│   ├── preload.php                # Pre-load initialization
│   ├── airtime-boot.php           # Airtime-specific boot
│   ├── check.php                  # System requirements check
│   ├── auth/                      # Auth adapters
│   │   ├── FreeIpa.php            # FreeIPA/LDAP auth
│   │   └── HeaderAuth.php         # Header-based auth
│   ├── common/                    # Utility classes (48 files)
│   │   ├── Assets.php
│   │   ├── AutoPlaylistManager.php
│   │   ├── CeleryManager.php
│   │   ├── Database.php
│   │   ├── DateHelper.php
│   │   ├── FileDataHelper.php
│   │   ├── FileIO.php
│   │   ├── HTTPHelper.php
│   │   ├── LocaleHelper.php
│   │   ├── PodcastManager.php
│   │   ├── SecurityHelper.php
│   │   ├── SessionHelper.php
│   │   ├── Storage.php
│   │   ├── TaskManager.php
│   │   ├── Timezone.php
│   │   ├── TuneIn.php
│   │   ├── UsabilityHints.php
│   │   └── WidgetHelper.php
│   ├── configs/                   # Configuration
│   │   ├── application.ini        # ZF1 application config
│   │   ├── conf.php               # Main config (Symfony Config)
│   │   ├── constants.php          # Constants
│   │   ├── ACL.php                # Access control lists
│   │   ├── navigation.php         # Menu navigation
│   │   └── classmap-airtime-conf.php
│   ├── controllers/               # MVC Controllers (26 files)
│   │   ├── ApiController.php
│   │   ├── DashboardController.php
│   │   ├── LibraryController.php
│   │   ├── LoginController.php
│   │   ├── PlaylistController.php
│   │   ├── ScheduleController.php
│   │   ├── UserController.php
│   │   └── plugins/               # Controller plugins
│   │       ├── Acl_plugin.php
│   │       ├── Maintenance.php
│   │       ├── PageLayoutInitPlugin.php
│   │       └── RabbitMqPlugin.php
│   ├── forms/                     # Zend_Form (35+ forms)
│   │   ├── Login.php
│   │   ├── AddUser.php
│   │   ├── EditUser.php
│   │   ├── AddShow*.php           # Multiple show forms
│   │   ├── Preferences.php
│   │   ├── customfilters/         # Custom form filters
│   │   ├── customvalidators/      # Custom validators
│   │   └── helpers/               # Form helpers
│   ├── layouts/                   # View layouts (.phtml)
│   ├── logging/                   # Logging
│   │   ├── AirtimeLog.php
│   │   └── Logging.php
│   ├── models/                    # Business logic + ORM
│   │   ├── airtime/               # Propel generated models
│   │   │   ├── om/                # Object Model (Base* classes)
│   │   │   ├── map/               # Table maps
│   │   │   └── [60+ Table].php    # Model classes
│   │   ├── formatters/            # Data formatters
│   │   └── tests/                 # Old test files (legacy)
│   ├── modules/rest/              # REST API module
│   │   ├── Bootstrap.php
│   │   ├── controllers/           # REST controllers
│   │   │   ├── MediaController.php
│   │   │   ├── PodcastController.php
│   │   │   └── RouteController.php
│   │   └── helpers/RestAuth.php
│   ├── services/                  # Service layer (11 services)
│   │   ├── CalendarService.php
│   │   ├── CeleryServiceFactory.php
│   │   ├── HistoryService.php
│   │   ├── MediaService.php
│   │   ├── PodcastService.php
│   │   ├── SchedulerService.php
│   │   ├── ShowFormService.php
│   │   ├── ShowService.php
│   │   └── UserService.php
│   ├── validate/                  # Validators
│   └── views/                     # View scripts (.phtml)
├── build/                         # Propel build configuration
│   ├── build.properties
│   └── schema.xml
├── install/                       # Installation files
├── locale/                        # i18n (16 languages)
├── public/                        # Document root
├── tests/                         # PHPUnit tests
│   ├── application/
│   │   ├── bootstrap.php          # Test bootstrap
│   │   ├── helpers/
│   │   │   ├── AirtimeInstall.php
│   │   │   └── TestHelper.php
│   │   ├── models/
│   │   │   ├── database/          # DB integration tests
│   │   │   │   ├── BlockDbTest.php
│   │   │   │   └── ScheduleDbTest.php
│   │   │   └── unit/              # Unit tests
│   │   │       ├── PreferenceUnitTest.php
│   │   │       └── ScheduleUnitTest.php
│   │   ├── services/
│   │   │   ├── database/          # Service DB tests
│   │   │   │   └── ShowServiceDbTest.php
│   │   │   └── unit/              # Service unit tests
│   │   │       └── ShowServiceUnitTest.php
│   │   └── testdata/              # Test data providers
│   ├── config/
│   │   └── config.yml             # Test configuration
│   └── phpunit.xml                # PHPUnit configuration
├── composer.json
├── composer.lock
├── Makefile
└── .php-cs-fixer.php
```

---

## 6. DATABASE REQUIREMENTS

### PostgreSQL Schema (60+ tables via Propel)

#### Core Tables
| Table | Purpose |
|-------|---------|
| cc_files | Audio file metadata |
| cc_playlist | Playlist definitions |
| cc_playlistcontents | Playlist track ordering |
| cc_block | Smart block definitions |
| cc_blockcontents | Smart block content |
| cc_blockcriteria | Smart block criteria |
| cc_show | Show definitions |
| cc_show_instances | Show occurrences |
| cc_show_days | Show repeat patterns |
| cc_show_schedule | Show content scheduling |
| cc_schedule | Master schedule |
| cc_subjs | Users/subjects |
| cc_access | ACL assignments |
| cc_pref | System preferences |
| cc_listener_count | Listener statistics |
| cc_playout_history | Play history |
| cc_webstream | Web stream definitions |
| cc_podcast | Podcast feeds |
| cc_podcast_episodes | Podcast episodes |
| celery_tasks | Celery task queue |
| sessions | PHP sessions |

### Test Database Setup
```yaml
test_database:
  name: airtimeunittests (configurable)
  privileges_required: [CREATE, DROP, INSERT, SELECT, UPDATE, DELETE]
  schema_generation: Via TestHelper::installTestDatabase()
  fixture_format: YAML (PHPUnit_Extensions_Database_DataSet_YamlDataSet)
```

---

## 7. TESTING INFRASTRUCTURE

### Current State
```yaml
testing_status:
  existing_test_files: ~10
  test_frameworks: ["PHPUnit 5.7", "Zend_Test_PHPUnit"]
  coverage: "<5%"
  coverage_tool: "Disabled (autoloader issues)"
  db_test_framework: "PHPUnit_Extensions_Database (YAML fixtures)"
```

### Test Types Required for 100% Coverage
1. **Unit Tests** — Services, helpers, formatters (no DB)
2. **Database Tests** — Models (require Propel + PostgreSQL)
3. **Controller Tests** — MVC (require Zend_Test + DB)
4. **Integration Tests** — REST API endpoints

### Test Configuration (tests/phpunit.xml)
```xml
<phpunit bootstrap="./application/bootstrap.php" colors="true">
    <testsuite name="My Application Tests">
        <directory>./</directory>
    </testsuite>
    <filter>
        <whitelist>
            <directory suffix=".php">../application/</directory>
            <exclude>
                <directory suffix=".phtml">../application/</directory>
                <file>../application/Bootstrap.php</file>
                <file>../application/controllers/ErrorController.php</file>
            </exclude>
        </whitelist>
    </filter>
    <php>
        <env name="ENVIRONMENT" value="testing" />
        <env name="APPLICATION_ENV" value="testing" />
        <env name="LIBRETIME_UNIT_TEST" value="1" />
        <env name="LIBRETIME_CONFIG_DIR" value="./config" />
        <env name="LIBRETIME_LOG_DIR" value="./log" />
    </php>
</phpunit>
```

### Test Bootstrap Flow
```php
// tests/application/bootstrap.php
1. error_reporting(E_ALL | E_STRICT)
2. require preload.php
3. Set include paths (library, vendor, propel, etc)
4. Logging::setLogPath()
5. Propel::init() with airtime-conf-production.php
6. Zend_Session::start()
```

---

## 8. ENVIRONMENT VARIABLES

```bash
# Required
ENVIRONMENT=testing
APPLICATION_ENV=testing
LIBRETIME_UNIT_TEST=1
LIBRETIME_CONFIG_DIR=./config
LIBRETIME_LOG_DIR=./log

# Optional (defaults used if not set)
LIBRETIME_CONFIG_FILEPATH=/path/to/config.yml
LIBRETIME_LEGACY_ROOT=/path/to/legacy
```

---

## 9. CRITICAL CONSTRAINTS & LIMITATIONS

```yaml
constraints:
  - id: C1
    description: "PHP 7.4 ONLY — No migration to 8.x allowed (project frozen)"
    impact: Blocks all modernization
    
  - id: C2
    description: "PHPUnit 5.7 locked — Deprecated but migration breaks compatibility"
    impact: Cannot use modern PHPUnit features
    
  - id: C3
    description: "ZF1 is EOL — Using zf1s community fork for PHP 7.4 support"
    impact: Limited documentation, security risk
    
  - id: C4
    description: "Propel 1.6 legacy ORM — All models require active DB connection"
    impact: True unit testing impossible for models
    
  - id: C5
    description: "Session dependency — Zend_Session::start() required in bootstrap"
    impact: Complicates CLI testing
    
  - id: C6
    description: "Code coverage disabled due to autoloader issues"
    impact: Cannot measure coverage accurately
```

---

## 10. INSTALLATION & SETUP

### macOS (Homebrew)
```bash
# 1. Install PHP 7.4
tap shivammathur/php
brew install shivammathur/php/php@7.4

# 2. Install extensions
brew install php@7.4-pdo-pgsql php@7.4-pgsql php@7.4-xdebug

# 3. Install tools
brew install composer postgresql@12

# 4. Configure PATH
export PATH="/usr/local/opt/php@7.4/bin:$PATH"
export PATH="/usr/local/opt/php@7.4/sbin:$PATH"
export PATH="/usr/local/opt/postgresql@12/bin:$PATH"

# 5. Verify
php -v                    # PHP 7.4.x
php -m | grep pdo_pgsql   # Should show
php -m | grep xdebug      # Should show
```

### Project Setup
```bash
cd legacy/

# 1. Install dependencies
composer install \
    --no-interaction \
    --no-progress \
    --no-plugins \
    --no-scripts \
    --optimize-autoloader

# 2. Configure test database
cp tests/config/config.yml.dist tests/config/config.yml
# Edit: set PostgreSQL credentials for test DB

# 3. Create test database
createdb airtimeunittests

# 4. Run tests
cd tests && ../vendor/bin/phpunit

# Or via Makefile
make test
```

---

## 11. MAKEFILE TARGETS

```makefile
make vendor      # Install composer dependencies
make test        # Run PHPUnit tests
make format      # Run php-cs-fixer
make lint        # Run php-cs-fixer --dry-run
make build       # Production build (no-dev)
make propel-gen  # Regenerate Propel models
```

---

## 12. COVERAGE REPORTING ISSUE

Current phpunit.xml comment:
```xml
<!-- Disabling broken code coverage report. 
     It's not using our autoloader for some reason... -->
```

### To Enable Coverage
1. Fix autoloader path in coverage whitelist, OR
2. Switch to `pcov` extension (faster, simpler), OR
3. Use `xdebug` with proper `include_path` configuration

---

## 13. TESTING WORK ESTIMATE

| Metric | Value |
|--------|-------|
| Lines of Code | ~45,000 |
| Current Test Coverage | <5% |
| Existing Test Files | ~10 |
| Estimated Tests Needed | 800-1,200 |
| Time Estimate (single dev) | 3-6 months |
| Complexity | Very High |

### Priority Order for Testing
1. `Application_Service_ShowService` — Critical path
2. `Application_Service_SchedulerService` — Core functionality
3. `Application_Model_Block` — Smart blocks
4. `Application_Model_Schedule` — Scheduling logic
5. `Application_Model_Show` — Show management
6. Common helpers — `DateHelper`, `FileDataHelper`, etc.
7. Controllers — Lower priority (integration tests preferred)

---

*Report generated for LibreTime Legacy testing initiative.*  
*Status: FROZEN — Maintenance mode only, no modernization.*

---

# Dependency Graph
```yaml
dependency_graph:
  components:
    api:
      path: app/api/
      type: django-app
      deps: [sdk, postgres, rabbitmq]
      entry: api.manage:main
    worker:
      path: app/worker/
      type: celery-worker
      deps: [sdk, api, rabbitmq]
      entry: worker.main:cli
    analyzer:
      path: app/analyzer/
      type: cli-tool
      deps: [sdk]
      entry: analyzer.main:cli
    playout:
      path: app/playout/
      type: playout-engine
      deps: [sdk, liquidsoap]
      entry: playout.main:cli
    api-client:
      path: app/api-client/
      type: library
      deps: []
      entry: none
    sdk:
      path: src/sdk/
      type: shared-library
      deps: []
      entry: none
    legacy:
      path: legacy/
      type: php-app
      deps: [api]
      entry: legacy/public/index.php
      php_version: "7.4"
      framework: "Zend Framework 1 (zf1s)"
      orm: "Propel 1.6"
      test_framework: "PHPUnit 5.7"
      status: "frozen"
  edges:
    - from: worker
      to: api
      type: uses-models
    - from: playout
      to: api
      type: fetches-schedule
    - from: analyzer
      to: api
      type: uploads-metadata
    - from: api
      to: sdk
      type: imports
    - from: worker
      to: sdk
      type: imports
    - from: playout
      to: sdk
      type: imports
    - from: analyzer
      to: sdk
      type: imports
    - from: legacy
      to: api
      type: depends-on-django-api
```

# Class Hierarchy
```yaml
class_hierarchy:
  classes:
    api:
      - api.core.models.User
      - api.storage.models.File
      - api.storage.models.Library
      - api.schedule.models.Show
      - api.schedule.models.Playlist
      - api.schedule.models.SmartBlock
      - api.podcasts.models.Podcast
      - api.history.models.PlayoutHistory
    playout:
      - playout.player.schedule.Schedule
      - playout.player.queue.Queue
      - playout.liquidsoap.client.LiquidsoapClient
    worker:
      - worker.tasks.podcast.download_podcast
    legacy:
      - Application_Service_ShowService
      - Application_Service_SchedulerService
      - Application_Service_UserService
      - Application_Model_Block
      - Application_Model_Schedule
      - Application_Model_Show
      - Application_Model_ShowInstance
      - Application_Model_StoredFile
  interfaces: {}
```

# Data Flow Map
```yaml
data_flow:
  flows:
    schedule-creation:
      - User creates show/playlist via API or Legacy UI
      - API stores in PostgreSQL
      - Celery worker handles async tasks (podcast download)
    playout-execution:
      - Playout fetches schedule from API
      - Schedule cached locally for resilience
      - Liquidsoap plays audio files
      - Playout reports history back to API
    file-analysis:
      - User uploads file via API
      - Analyzer extracts metadata/replaygain
      - Results stored via API
    legacy-ui:
      - User interacts with ZF1 controllers
      - Forms validated with Zend_Form
      - Models use Propel ORM
      - REST module provides JSON API
```

# Database Schema Knowledge
```yaml
database:
  tables:
    core:
      - users
      - preferences
    storage:
      - files
      - libraries
    schedule:
      - shows
      - playlists
      - playlist-contents
      - smart-blocks
      - webstreams
    podcasts:
      - podcasts
      - podcast-episodes
    history:
      - playout-history
      - listener-stats
    legacy:
      - cc_files (Propel model)
      - cc_playlist (Propel model)
      - cc_show (Propel model)
      - cc_schedule (Propel model)
      - cc_block (Propel model)
      - cc_subjs (users)
      - cc_access (ACL)
  indexes: []
  relationships:
    - shows have many playlists
    - playlists have many files
    - users own shows/playlists
    - blocks have criteria
    - shows have instances (occurrences)
```

# Configuration Registry
```yaml
config:
  sources:
    pyproject.toml:
      scope: workspace
      tools: [black, ruff, mypy, pytest]
    etc/pre-commit.yaml:
      scope: linting
      hooks: [black, ruff, mypy, pyright, refurb, vulture, bandit, hexora]
    app/api/api/settings/:
      scope: django
      files: [base.py, testing.py, production.py]
    docker-compose.yml:
      scope: services
      services: [postgres, rabbitmq, liquidsoap]
    legacy/composer.json:
      scope: legacy-php
      php_version: "7.4"
      framework: "Zend Framework 1"
      orm: "Propel 1.6"
    legacy/tests/phpunit.xml:
      scope: legacy-testing
      bootstrap: "./application/bootstrap.php"
      coverage: "disabled"
  secrets:
    - .env (not committed)
    - UV_INDEX_PRIVATE_PASSWORD (for private package index)
```

# Testing Matrix
```yaml
testing:
  strategies:
    unit:
      runner: pytest
      location: app/*/tests/
      pattern: "*_test.py"
    integration:
      runner: pytest-django
      settings: api.settings.testing
      requires: [postgres]
    legacy:
      runner: phpunit
      version: "5.7 (deprecated)"
      location: legacy/tests/
      requires: [php-7.4, postgresql, pdo_pgsql]
      coverage: "<5%"
      target_coverage: "80%"
      bootstrap: "tests/application/bootstrap.php"
      docker: true
      docker_command: "./test.sh"
      docker_services: [postgres, php]
      plan: "legacy/TESTING_PLAN.md"
      plan_duration: "15 weeks"
      plan_tasks: "~120"
  fixtures:
    - app/api/api/_fixtures/
    - app/playout/tests/conftest.py
    - legacy/tests/application/testdata/
    - legacy/tests/application/models/database/datasets/
  mock_rules:
    - Use pytest-mock for unit tests
    - Use requests-mock for HTTP clients
    - Propel models require real database (cannot mock)
```

# Gotchas & Quirks
```yaml
gotchas:
  - id: G1
    description: Legacy PHP codebase uses Zend Framework 1 and Propel ORM
    impact: High — avoid modifications unless necessary
    workarounds: Prefer API changes over Legacy changes
  - id: G2
    description: Each app/* component has its own pyproject.toml
    impact: Medium — run commands from component directory
    workarounds: Use `cd app/<component> && uv run pytest`
  - id: G3
    description: Playout can operate independently if API is down
    impact: Low — schedule caching provides resilience
    workarounds: None needed, it's a feature
  - id: G4
    description: Some tests require Docker services (postgres, rabbitmq)
    impact: Medium — tests fail without services
    workarounds: Run `docker compose up -d` before testing
  - id: G5
    description: Legacy PHP is FROZEN on PHP 7.4 — no updates allowed
    impact: Critical — cannot modernize, stuck with deprecated PHPUnit 5.7
    workarounds: Write tests within existing constraints only
  - id: G6
    description: Propel models require active DB connection — no true unit testing
    impact: High — all model tests are integration tests
    workarounds: Test business logic in services separately
  - id: G7
    description: Code coverage disabled due to autoloader issues
    impact: Medium — cannot measure test coverage accurately
    workarounds: Fix phpunit.xml whitelist or switch to pcov
  - id: G8
    description: Docker testing environment created — no local PHP 7.4 required
    impact: High — enables testing without legacy stack installation
    workarounds: Use ./test.sh script for all testing operations
  - id: G9
    description: ViewSet.get_queryset() must filter by ownership for security
    impact: Critical — anonymous access if not implemented
    workarounds: Override get_queryset() in all ViewSets with ownership filtering
    refs: [app/api/api/schedule/views/show.py, app/api/api/schedule/views/webstream.py]
  - id: G10
    description: ModelViewSet performs_create() auto-assigns owner for CREATE
    impact: Medium — anonymous CREATE may succeed if queryset filtering missing
    workarounds: Check request.user.is_authenticated before auto-assigning
    refs: [app/api/api/schedule/views/show.py::perform_create]
  - id: G11
    description: Authorization header case sensitive - only "Api-Key" works
    impact: Low — clients using "api-key" or "API-KEY" will fail auth
    workarounds: Always use "Api-Key" exact case in client code
    refs: [app/api/api/permissions.py::check_authorization_header]
  - id: G12
    description: BOLA pattern - queryset.objects.all() without ownership filter
    impact: Critical — any user can access all users' data
    workarounds: Always add get_queryset() with owner filter; use check_authorization_header
    refs: [.agent/research/bola_investigation_t806_t854.md]
  - id: G13
    description: Nested resources inherit parent ownership - filter via parent FK
    impact: High — child resources may leak if parent ownership not checked
    workarounds: Filter nested resources by parent__owner=user
    refs: [app/api/api/schedule/views/playlist.py::PlaylistContentViewSet]
  - id: G14
    description: Permission check flow — complex multi-layer system
    impact: Medium — hard to debug, easy to miss edge cases
    workarounds: See .agent/research/permissions_inventory.md for full flow
    refs: [.agent/research/permissions_inventory.md]
  - id: G15
    description: get_own_obj() bug — checks entire table, not specific object
    impact: Critical — HOST role permissions may work incorrectly
    workarounds: Don't rely on own_* for security; add explicit queryset filters
    refs: [app/api/api/permissions.py::get_own_obj]
```

# Insights & Patterns
```yaml
insights:
  - id: I1
    category: architecture
    description: Clear separation between "create schedule" and "play schedule" blocks
    confidence: high
    refs: [app/api/, app/playout/]
  - id: I2
    category: packaging
    description: UV workspace with monorepo structure (app/*, src/*)
    confidence: high
    refs: [pyproject.toml, uv.lock]
  - id: I3
    category: code-quality
    description: Extensive pre-commit hooks including security (bandit, hexora)
    confidence: high
    refs: [etc/pre-commit.yaml]
  - id: I4
    category: external-deps
    description: Liquidsoap integration is external binary dependency
    confidence: high
    refs: [app/playout/playout/liquidsoap/]
  - id: I5
    category: legacy-constraints
    description: Legacy testing requires full LAMP stack (PHP 7.4, PostgreSQL, extensions)
    confidence: high
    refs: [legacy/, legacy/tests/]
  - id: I6
    category: testing-strategy
    description: PHPUnit 5.7 + Zend_Test requires database for most tests
    confidence: high
    refs: [legacy/tests/phpunit.xml]
  - id: I7
    category: infrastructure
    description: Docker-based testing eliminates local PHP 7.4 dependency
    confidence: confirmed
    refs: [legacy/Dockerfile.test, legacy/docker-compose.test.yml, legacy/test.sh]
    details:
      - PHP 7.4 + Xdebug 2.9.8 in container
      - PostgreSQL 12 as test database
      - One-shot and interactive test runners
      - Coverage reports in ./coverage/
  - id: I8
    category: planning
    description: 15-week testing roadmap created for 80% legacy coverage
    confidence: confirmed
    refs: [legacy/TESTING_PLAN.md]
    details:
      - ~120 atomic tasks across 10 phases
      - Critical path prioritizes ShowService, Schedule, UserService
      - 8-10 tasks/week pace for single developer
      - Foundation → Helpers → Services → Models → Forms → Controllers
  - id: I9
    category: testing-gotchas
    description: DRF APIClient credentials() has priority over defaults[]
    confidence: confirmed
    refs: [app/api/api/tests/test_credentials_vs_defaults.py]
    details:
      - "client.credentials(HTTP_AUTHORIZATION='Api-Key X')" takes precedence
      - "client.defaults['HTTP_AUTHORIZATION'] = 'Bearer Y'" does NOT override
      - To override auth, use credentials() again, not defaults[]
      - Critical for redteam auth bypass testing - false positives possible
  - id: I10
    category: security
    description: IsSystemTokenOrUser permission correctly rejects invalid tokens
    confidence: confirmed
    refs: [app/api/api/permissions.py]
    details:
      - Invalid Bearer tokens correctly return 403
      - Malformed Api-Key headers handled safely (no IndexError)
      - Session auth and API-Key auth properly separated
      - Previous "bypass" reports were test methodology bugs, not permission bugs
  - id: I12
    category: security-pattern
    description: BOLA fix pattern - Three-tier ownership filtering
    confidence: confirmed
    refs: [.agent/research/bola_investigation_t806_t854.md, app/api/api/schedule/views/show.py]
    details:
      - Pattern: Service auth (API-Key) = full access
      - Pattern: Anonymous = empty queryset (objects.none())
      - Pattern: Superuser = full access
      - Pattern: Regular user = filter by owner=user (or hosts__user for M2M)
      - Critical: Must override get_queryset(), not just rely on queryset attr
  - id: I11
    category: security-bug
    description: Authorization header case sensitivity violates RFC 7230
    confidence: confirmed
    refs: [app/api/api/schedule/tests/views/test_webstream_permissions_redteam_t249.py]
    details:
      - "Api-Key token" works (200)
      - "api-key token" fails (403)
      - "API-KEY token" fails (403)
      - RFC 7230 section 3.2: "Each header field consists of a case-insensitive field name"
      - Bug in check_authorization_header() or DRF request.headers access
```

# Investigation Log
```yaml
investigation_log:
  - id: INV-001
    topic: "Legacy PHP testing prerequisites analysis"
    status: resolved
    conclusion: "Complete inventory created — PHP 7.4, PostgreSQL, PHPUnit 5.7, ZF1, Propel 1.6"
    discovered: "2026-04-07T13:16:18Z"
    resolved: "2026-04-07T13:16:18Z"
  - id: INV-002
    topic: "Docker-based testing environment for legacy PHP"
    status: resolved
    conclusion: "Created full Docker setup — Dockerfile, docker-compose, test.sh script, no local PHP required"
    discovered: "2026-04-07T13:45:00Z"
    resolved: "2026-04-07T13:45:00Z"
  - id: INV-003
    topic: "Comprehensive testing plan for legacy coverage"
    status: resolved
    conclusion: "Created 15-week, ~120 task roadmap for 80% coverage — see TESTING_PLAN.md"
    discovered: "2026-04-07T19:00:00Z"
    resolved: "2026-04-07T19:00:00Z"
  - id: INV-004
    topic: "T575-T600: Invalid token bypass vulnerability investigation"
    status: resolved
    conclusion: "NOT A BUG — test methodology error. DRF APIClient credentials() has priority over defaults[]"
    discovered: "2026-04-10T21:30:00Z"
    resolved: "2026-04-10T22:08:00Z"
    details:
      - Initial report: Schedule endpoints return 200 with invalid Bearer token
  - id: INV-005
    topic: "Authorization header case sensitivity"
    status: open
    conclusion: "RFC 7230 violation — header names should be case-insensitive but 'api-key' fails"
    discovered: "2026-04-10T22:50:00Z"
    details:
      - Test test_auth_case_sensitivity discovered inconsistent behavior
      - "Api-Key token" returns 200, "api-key token" returns 403
      - RFC 7230 section 3.2: header field names are case-insensitive
      - Likely in check_authorization_header() string comparison
  - id: INV-006
    topic: "BOLA vulnerabilities in Playlist/SmartBlock/File ViewSets"
    status: in_progress
    conclusion: "API1:2023 BOLA - Multiple ViewSets missing ownership filtering"
    discovered: "2026-04-10T23:00:00Z"
    details:
      - Full investigation: .agent/research/bola_investigation_t806_t854.md
      - Affected: PlaylistViewSet, SmartBlockViewSet, FileViewSet
      - Pattern: Missing get_queryset() with owner filter
      - Impact: Any user can CRUD any other user's data
      - Fix pattern: Use Show/Webstream implementation as reference
      - Nested resources also affected: PlaylistContent, SmartBlockContent, SmartBlockCriteria
  - id: INV-007
    topic: "Complete permissions system inventory"
    status: completed
    conclusion: "Full mapping of DRF permissions, Django permissions, role-based access"
    discovered: "2026-04-10T23:30:00Z"
    details:
      - Documents: .agent/research/permissions_inventory.md
      - Matrix: .agent/research/permissions_matrix.md
      - 2 DRF permission classes: IsSystemTokenOrUser, IsAdminOrOwnUser
      - 4 Roles: GUEST (15 perms), HOST (44 perms), MANAGER (43+ perms), ADMIN
      - 11 custom model permissions for own_* access
      - 31+ ViewSets, most using default IsSystemTokenOrUser
      - Critical bug: get_own_obj() checks entire table, not specific object
  - id: INV-008
    topic: "Role-based permission test suite created"
    status: completed
    conclusion: "126 test cases covering all roles and BOLA prevention"
    discovered: "2026-04-10T23:45:00Z"
    details:
      - 6 test files in app/api/api/tests/
      - GUEST: 25 tests (read-only)
      - HOST: 34 tests (own content)
      - MANAGER: 30 tests (full CRUD)
      - ADMIN: 25 tests (superuser)
      - BOLA: 12 tests (cross-role prevention)
      - Fixtures: role_fixtures.py with all role clients
      - Documentation: role_based_tests_documentation.md
```

# Uncertainty Registry
```yaml
unknowns:
  - id: U1
    topic: "Exact test data requirements for 100% coverage"
    blocking: false
    notes: "Will discover during test implementation"
```

# Deprecated Knowledge
```yaml
deprecated: []
```

# Performance Baselines
```yaml
performance:
  benchmarks: []
```

# External Dependencies
```yaml
third_party:
  django:
    version: ">=4.2.0,<4.3"
    purpose: Web framework and ORM
  djangorestframework:
    version: ">=3.14.0,<3.16"
    purpose: REST API
  celery:
    purpose: Async task queue
    notes: Via worker component
  psycopg:
    version: ">=3.1.8,<3.3"
    purpose: PostgreSQL driver
  gunicorn:
    purpose: WSGI server
  uvicorn:
    purpose: ASGI server
  sentry-sdk:
    purpose: Error tracking
  liquidsoap:
    purpose: Audio streaming engine
    notes: External binary, not Python package
  legacy_php:
    php: "^7.4 (frozen)"
    framework: "Zend Framework 1 (zf1s ^1.13)"
    orm: "Propel 1.6 (libretime fork)"
    test_framework: "PHPUnit 5.7 (deprecated, locked)"
    database: "PostgreSQL 12+"
```

# Health Check Endpoints
```yaml
health:
  - endpoint: /api/health
    type: http
    checks: [database, celery]
```

# Critical Paths & Failure Domains
```yaml
critical_paths:
  - path: playout → liquidsoap → icecast
    description: Audio streaming chain
    failure_impact: Complete broadcast outage
  - path: legacy → api → postgres
    description: Legacy UI depends on Django API
    failure_impact: Web UI non-functional
single_points_of_failure:
  - component: liquidsoap
    mitigation: Can restart independently
  - component: postgres
    mitigation: Playout caches schedule locally
  - component: php-7.4-runtime
    mitigation: Legacy frozen, no upgrade path
```

# Auto-Update Rules
```yaml
maintenance:
  auto_update_triggers:
    - file_changed: "**/models/*.py"
      update_section: database
    - file_changed: "**/repositories/*.py"
      update_section: [class_hierarchy, dependency_graph]
    - file_changed: "**/services/*.py"
      update_section: dependency_graph
    - file_changed: "**/routers/*.py"
      update_section: [dependency_graph, data_flow]
    - file_changed: "pyproject.toml"
      update_section: third_party
    - file_changed: "legacy/**"
      update_section: [dependency_graph, gotchas, insights]
  
  validation_rules:
    - rule: "All repository classes must have entry in class_hierarchy"
      severity: warning
    - rule: "All service dependencies must be in dependency_graph"
      severity: warning
```

---

# LEGACY TESTING PLAN — 15 Week Coverage Roadmap

> **Location**: `legacy/TESTING_PLAN.md`  
> **Total Tasks**: ~120 atomic items  
> **Duration**: 15 weeks (1 developer)  
> **Target Coverage**: 80%  
> **Pace**: 8-10 tasks/week

## Phase Overview

| Phase | Weeks | Tasks | Focus Area |
|-------|-------|-------|------------|
| 0. Foundation | 1-2 | 12 | Infrastructure, fixtures, path fixes |
| 1. Common Helpers | 2-3 | 18 | DateHelper, FileDataHelper, SecurityHelper |
| 2. Service Layer | 3-5 | 27 | ShowService, SchedulerService, UserService |
| 3. Models | 5-7 | 30 | Show, Schedule, Block, Playlist, User |
| 4. Forms | 7-8 | 15 | Validation, form processing |
| 5. Auth & Security | 8-9 | 12 | Authentication, ACL, validators |
| 6. Controllers | 9-11 | 25 | MVC controllers, AJAX endpoints |
| 7. Integration | 11-12 | 13 | End-to-end scenarios, edge cases |
| 8. REST API | 12-13 | 9 | REST module endpoints |
| 9. Formatters | 13-14 | 4 | Data formatters |
| 10. Final | 14-15 | 6 | Coverage analysis, docs |

## Critical Path Priority

### Week 1-2: Foundation
- Fix test paths (PreferenceUnitTest.php, bootstrap.php)
- Create TestBootstrap.php, ModelFactory
- Create YAML fixtures for User, Show, File

### Week 3-4: Service Core
- ShowService::addUpdateShow() — all repeat types
- ShowService::deleteShow() — single/current/all
- SchedulerService::scheduleAfter(), removeGaps()

### Week 5-6: Models Core
- Show Model — CRUD, hosts, recording flag
- ShowInstance — schedule manipulation
- Schedule — overlap detection
- Block — smart block criteria

### Week 7-8: Complete Services + Forms
- UserService — full CRUD
- MediaService — upload flow
- Forms — AddShow*, Login, AddUser

## Key Files to Test First

```
application/services/ShowService.php          # CRITICAL
application/services/SchedulerService.php     # CRITICAL
application/models/Show.php                   # CRITICAL
application/models/ShowInstance.php           # CRITICAL
application/models/Schedule.php               # CRITICAL
application/common/DateHelper.php             # HIGH
application/common/FileDataHelper.php         # HIGH
application/common/SecurityHelper.php         # HIGH
```

## Testing Conventions

```php
// Test class naming
class ShowServiceTest extends PHPUnit_Framework_TestCase

// Test method naming
test<MethodName>_<Condition>_<ExpectedResult>()
// Example: testAddUpdateShow_WeeklyRepeat_CreatesInstances()

// Run tests
cd legacy && ./test.sh test

// Run specific test
cd legacy && ./test.sh phpunit --filter testAddUpdateShow
```

## Success Metrics by Phase

| Phase | Target | Current | Status |
|-------|--------|---------|--------|
| Foundation | 90% | TBD | 🔄 |
| Helpers | 90% | TBD | 🔄 |
| Services | 85% | <5% | 🔄 |
| Models | 80% | <5% | 🔄 |
| Forms | 75% | 0% | 🔄 |
| Controllers | 70% | 0% | 🔄 |
| **TOTAL** | **80%** | **<5%** | 🚀 |

---

# Usage Instructions for Agents

## When starting session:
1. Read this file entirely — it's structured for fast parsing
2. Check `investigation_log` for relevant solved problems
3. Note `unknowns` that might affect current task
4. Review `critical_paths` if changing infrastructure

## When discovering new knowledge:
1. **STOP and WRITE** — no batching, no "later"
2. Identify correct YAML section
3. Append/update with timestamp
4. If replacing old knowledge → move to `deprecated`
5. If investigation completes → update status, add conclusion

## MANDATORY Write Triggers (ALWAYS WRITE)

| Action | Required Entry |
|--------|----------------|
| Grep finished | Pattern insight → `insights` |
| File read | Component → `dependency_graph` |
| Bug found | Gotcha → `gotchas` |
| Discussion | Domain knowledge → `insights` |
| Debug session | Investigation → `investigation_log` |
| User explains | Context → `insights` |
| "Aha!" moment | Insight → `insights` |
| Fix applied | Conclusion → `investigation_log` |

### The "Puffy Knowledge Base" Rule
- Minimum: 1 entry per 10 minutes of work
- Target: 10-50 lines added per hour
- Success: File size grows every session
- **If it's not growing, you're not writing enough**

## Forbidden (NEVER DO)
- ❌ "I'll add this at the end"
- ❌ "This is too small"
- ❌ "I remember this"
- ❌ Batch updates
- ❌ "This is obvious"

## API v2 Migration Analysis (FastAPI)

### Database Schema (managed=False tables)
- **core**: cc_subjs, cc_subjs_token, cc_login_attempts, cc_pref, cc_service_register, third_party_track_references, celery_tasks
- **storage**: cc_files (50+ fields!), cc_track_types
- **schedule**: cc_show, cc_show_hosts, cc_show_days, cc_show_instances, cc_show_rebroadcast, cc_playlist, cc_playlistcontents, cc_block, cc_blockcontents, cc_blockcriteria, cc_webstream, cc_webstream_metadata, cc_schedule
- **history**: cc_listener_count, cc_timestamp, cc_mount_name, cc_live_log, cc_playout_history, cc_playout_history_metadata, cc_playout_history_template, cc_playout_history_template_field
- **podcasts**: podcast, podcast_episodes, station_podcast, imported_podcast

### Key Migration Challenges
1. MD5 password hashing in User model
2. Read/Write serializer pattern (Schedule uses different serializers for GET vs POST)
3. File model has 50+ fields
4. Complex permission system with "own_" prefix
5. Custom download action (X-Accel-Redirect)
6. Dual auth: session for users, API-Key for services

### Full Report
See agent analysis output for complete endpoint mapping, pydantic schemas, and permission matrix.

---

## Reference Documents

Critical reference documentation for API v2 and FastAPI migration.

### API v2 FastAPI Migration Report

```yaml
reference_document:
  id: api_v2_fastapi_migration_report
  title: "API v2 FastAPI Migration Analysis Report"
  path: .agent/research/api_v2_fastapi_migration_report.md
  size: 45KB
  lines: 1246
  created: 2026-04-07T17:00:00Z
  
  contents:
    - section: "Django models with db_column mappings"
    - section: "Pydantic schemas for FastAPI"
    - section: "45+ endpoints with methods"
    - section: "Permission system (IsSystemTokenOrUser, IsAdminOrOwnUser)"
    - section: "Read/Write serializer patterns"
    - section: "SQLAlchemy Table definitions"
  
  modules_covered:
    - core: "Users, Preferences, Auth, Public endpoints"
    - storage: "Files, Libraries"
    - schedule: "Shows, Playlists, SmartBlocks, Schedule, Webstreams"
    - history: "PlayoutHistory, ListenerCount, LiveLog"
    - podcasts: "Podcasts, Episodes"
  
  critical_patterns:
    - "ReadWriteSerializerMixin for Schedule (GET vs POST different schemas)"
    - "Dual auth: Session + Api-Key"
    - "X-Accel-Redirect for file download"
    - "MD5 password hashing (legacy)"
```

### API v2 Test Coverage Plan

```yaml
reference_document:
  id: api_v2_test_coverage_plan
  title: "API v2 Comprehensive Test Coverage Plan"
  path: .agent/research/api_v2_test_coverage_plan.md
  size: 22KB
  created: 2026-04-07T18:45:00Z
  linked_tasks: T153-T307
  
  purpose: "Contract tests for Django→FastAPI migration"
  test_count: 155
  
  sections:
    - infrastructure: "T153-T162 - Fixtures and factories"
    - core_module: "T163-T184 - Users, Preferences, Auth"
    - storage_module: "T186-T200 - Files (CRITICAL)"
    - schedule_module: "T201-T258 - Shows, Playlists, Schedule (CRITICAL)"
    - history_module: "T259-T267 - Playout history"
    - podcasts_module: "T268-T278 - Podcasts"
    - auth_tests: "T279-T283 - Session + Api-Key"
    - edge_cases: "T284-T298 - Serializers, validation"
    - documentation: "T299-T307 - Guides and benchmarks"
  
  critical_path:
    - "T153-T162: Infrastructure"
    - "T186-T194: Files (especially T193 download)"
    - "T201-T258: Schedule (complex relationships)"
    - "T279-T283: Authentication"
    - "T284: ReadWriteSerializerMixin behavior"
  
  infrastructure_complete: true
  estimated_time: "2-3 weeks full-time"
```

### Quick Access

| Document | Purpose | Path |
|----------|---------|------|
| Migration Report | Schema mapping, Pydantic models, SQLAlchemy | `.agent/research/api_v2_fastapi_migration_report.md` |
| Test Coverage Plan | 155 test tasks, endpoint matrix, critical path | `.agent/research/api_v2_test_coverage_plan.md` |


---

## Test Environment (Docker Compose)

```yaml
test_environment:
  file: docker-compose.test.yml
  type: isolated_ephemeral
  data_persistence: false  # tmpfs for postgres
  
  services:
    postgres:
      image: postgres:15-alpine
      port: 5432
      credentials:
        user: libretime
        password: libretime
        database: libretime_test
      
    rabbitmq:
      image: rabbitmq:3.13-alpine
      port: 5672
      credentials:
        user: libretime
        password: libretime
        vhost: /libretime
      
    redis:
      image: redis:7-alpine
      port: 6379
      purpose: cache_sessions_future

  commands:
    start: "docker compose -f docker-compose.test.yml up -d"
    status: "docker compose -f docker-compose.test.yml ps"
    stop: "docker compose -f docker-compose.test.yml down"
    logs: "docker compose -f docker-compose.test.yml logs -f"

  test_execution:
    setup: |
      docker compose -f docker-compose.test.yml up -d
      sleep 5  # Wait for services
    
    run_tests: |
      cd app/api
      uv run pytest api/core/tests/models/ -v
      uv run pytest api/tests/test_permissions.py -v
    
    teardown: |
      docker compose -f docker-compose.test.yml down

  django_settings:
    database:
      engine: django.db.backends.postgresql
      host: localhost
      port: 5432
      name: libretime_test
      user: libretime
      password: libretime
    
    test_runner: api.tests.runner.ManagedModelTestRunner
    migrations: auto_applied
```


---

## Datetime Handling in API Tests (Timezone-Aware)

**Setup:** `USE_TZ = True` and `DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"` in REST_FRAMEWORK.

**Problem:** `model_bakery` creates datetime with microseconds, DRF serializes seconds only.

**Symptom:**
```
AssertionError: datetime.datetime(2026, 4, 9, 11, 51, 28) != datetime.datetime(2026, 4, 9, 11, 51, 28, 860000)
```

**Solution:** Use helpers to zero microseconds:

```python
from django.utils.timezone import now
from sdk import format_datetime

def now_seconds():
    """Return current time with microseconds zeroed."""
    return now().replace(microsecond=0)

# In test:
show = baker.make(
    "schedule.ShowInstance",
    starts_at=now_seconds() - timedelta(minutes=5),
    ends_at=now_seconds() + timedelta(minutes=5),
)

# For query params use format_datetime:
range_start = format_datetime(now_seconds() - timedelta(minutes=1))
```

**Files:**
- `app/api/api/settings/testing.py` — USE_TZ=True, DATETIME_FORMAT
- `app/api/api/schedule/tests/views/test_schedule.py` — T308-T311 fixed
- `src/sdk/sdk/datetime.py` — format_datetime() helper

**API datetime format:** All datetimes returned with Z suffix (UTC), e.g., `2026-04-09T12:00:00Z`
---
name: knowledge
---

# Project Knowledge

Critical information learned during development.

## Django + DRF Testing with Timezone-Aware Datetimes

**Problem:** model_bakery creates timezone-aware datetimes with microseconds; DRF serializes to seconds-only ISO format with Z suffix. Direct comparison fails.

**Example failure:**
```python
AssertionError: datetime.datetime(2026, 4, 9, 11, 51, 28) != datetime.datetime(2026, 4, 9, 11, 51, 28, 860000)
```

**Solution:** Use helpers to zero microseconds:

```python
from django.utils.timezone import now
from sdk import format_datetime

def now_seconds():
    """Return current time with microseconds zeroed."""
    return now().replace(microsecond=0)

# In test:
show = baker.make(
    "schedule.ShowInstance",
    starts_at=now_seconds() - timedelta(minutes=5),
    ends_at=now_seconds() + timedelta(minutes=5),
)

# For query params use format_datetime:
range_start = format_datetime(now_seconds() - timedelta(minutes=1))
```

**Files:**
- `app/api/api/settings/testing.py` — USE_TZ=True, DATETIME_FORMAT
- `app/api/api/schedule/tests/views/test_schedule.py` — T308-T311 fixed
- `src/sdk/sdk/datetime.py` — format_datetime() helper

**API datetime format:** All datetimes returned with Z suffix (UTC), e.g., `2026-04-09T12:00:00Z`


## Storage Module Known Bugs (T316-T318)

### T316: File DELETE doesn't remove DB record
**Location:** `app/api/api/storage/views/file.py:perform_destroy()`
**Bug:** Method removes file from disk via `os.remove()` but missing `instance.delete()` call.
**Impact:** DELETE returns 204, file gone from disk, but DB record persists. Double DELETE returns 204 instead of 404.
**Tests:** `test_file_delete.py::test_delete_file_removes_from_db` (xfail)

### T317: File download crashes on None filepath
**Location:** `app/api/api/storage/views/file.py:download()`
**Bug:** `os.path.join("/api/_media", instance.filepath)` fails with TypeError when `filepath=None`.
**Impact:** 500 Internal Server Error instead of 404.
**Tests:** `test_file_download.py::test_download_no_filepath` (xfail)

### T318: Library DELETE fails with FK constraint
**Location:** `app/api/api/storage/models/file.py` and `app/api/api/storage/models/library.py`
**Bug:** File.library (db_column="track_type_id") uses `DO_NOTHING` on delete. When deleting Library with associated Files, FK constraint violation occurs.
**Impact:** DELETE /api/v2/libraries/{id} returns 500 if library has files.
**Root cause:** Database-level constraint `cc_files_track_type_fkey` on `cc_files.track_type_id`.
**Possible fixes:**
1. Use `SET_NULL` instead of `DO_NOTHING` on File.library FK
2. Pre-check in view and return 409 Conflict if files exist
3. Cascade delete files with library (destructive)
**Tests:** `test_library_delete.py::test_delete_library_with_files_*` (3 xfail tests)


## Library Model DB Constraints

**Mismatch between Django model and DB schema:**

| Field | Django Model | Database | Issue |
|-------|--------------|----------|-------|
| `description` | `null=True, blank=True` | `NOT NULL` | CREATE without description crashes (T198) |
| `type_name` | `max_length=255` | `varchar(64)` | Name > 64 chars crashes (T199) |

**Tests documenting this:** `test_library_create.py` — 3 xfail tests


## Test Count Summary

| Section | Tasks | Tests | Passed | XFail |
|---------|-------|-------|--------|-------|
| Section 1 (T173-T181) | 9 | 133 | 128 | 5 |
| Section 2 (T182-T184) | 3 | 51 | 51 | 0 |
| Section 3 (T185-T200) | 16 | 241 | 222 | 19 |
| **Total** | **28** | **425** | **401** | **24** |


## API Test Suite Completion — T279-T307

**Archived:** 2026-04-09T21:03:16Z — All tasks T279-T307 moved to Archive

### Tests Added by Section

| Section | Tasks | Tests | Passed | XFailed |
|---------|-------|-------|--------|---------|
| Auth Tests (T279-T283) | 5 | 43 | 40 | 3 |
| Edge/Integration (T284-T298) | 15 | 157 | 155 | 2 |
| Documentation (T299-T307) | 9 | 119 | 118 | 1 |
| **Total** | **29** | **319** | **313** | **6** |

### Key Test Files Created

| File | Purpose | Tests |
|------|---------|-------|
| `test_auth_session.py` | Session authentication | 9 |
| `test_auth_apikey.py` | Api-Key authentication | 13 |
| `test_auth_public.py` | Public endpoints | 6 |
| `test_auth_invalid.py` | Invalid auth handling | 9 |
| `test_schedule_overbooked.py` | Overbooked filter | 4 |
| `test_show_days_repeat_patterns.py` | Instance generation | 25 |
| `test_playlist_length.py` | Length field | 6 |
| `test_smart_block_kind.py` | Dynamic/static kinds | 6 |
| `test_file_unique.py` | Unique constraints | 5 |
| `test_cascade_deletes.py` | Delete behavior | 7 |
| `test_pagination.py` | Pagination disabled | 5 |
| `test_concurrent_edits.py` | Concurrency | 12 |
| `test_large_payload.py` | Performance | 15 |
| `test_fixtures_docs.py` | Fixtures docs | 25 |
| `test_run_docs.py` | Test running docs | 29 |
| `test_contract_guide.py` | Contract testing | 22 |

### Active Bug Tasks

| ID | Bug | Location | Impact |
|----|-----|----------|--------|
| T308 | `is_superuser()` TypeError | `IsAdminOrOwnUser.has_permission()` | 500 on unauthenticated requests |
| T341 | `IndexError` on empty Api-Key | `check_authorization_header()` | 500 on `Authorization: Api-Key ` |

**Tests confirming bugs:** `test_auth_session.py::TestBugT308`, `test_auth_apikey.py::TestBugT341`


## Datetime Formatting Standard — T342

**Standard:** Use `sdk.format_datetime()` for all timezone-aware datetime formatting in tests.

**Helper:** `src/sdk/sdk/datetime.py::format_datetime(dt: datetime) -> str`

**Rules:**
1. Always use `format_datetime()` instead of `.isoformat().replace('+00:00', 'Z')`
2. Always use `format_datetime(now())` instead of `now().isoformat()`
3. Import: `from sdk.datetime import format_datetime`

**Before (incorrect):**
```python
new_start = (start_time + timedelta(hours=2)).isoformat().replace('+00:00', 'Z')
"created": now().isoformat()
```

**After (correct):**
```python
new_start = format_datetime(start_time + timedelta(hours=2))
"created": format_datetime(now())
```

**Files updated in T342:**
- `api/schedule/tests/views/test_show_instance_update.py` — 6 replacements
- `api/core/tests/views/test_auth.py` — 4 replacements


## Naive Datetime Warnings in Tests — T343 Investigation

**Issue:** model_bakery generates naive datetime for DateTimeField by default, causing Django RuntimeWarning when USE_TZ=True.

**Warning Pattern:**
```
RuntimeWarning: DateTimeField {Model}.{field} received a naive datetime (2026-04-09 10:00:00) while time zone support is active.
```

**Affected Models (API):**
- ShowInstance (created_at, starts_at, ends_at)
- Webstream (created_at, updated_at)
- Schedule (starts_at, ends_at)
- PlayoutHistory (starts)
- LiveLog (start_time)

**Solution:** Configure model_bakery in conftest.py:
```python
from django.utils import timezone
from model_bakery import baker

# Configure baker to use timezone-aware datetimes
baker.generators.add('DateTimeField', lambda: timezone.now())
```

**Alternative (per-test fix):**
```python
from django.utils.timezone import now

instance = baker.make(
    ShowInstance,
    starts_at=now(),  # Explicit timezone-aware
    ends_at=now(),
)
```

**Files with warnings:** 7 test files, 23 test cases, 43 total warnings


## Test Isolation Patterns — T344

**Problem:** Hardcoded unique values in tests cause failures when tests run in sequence.

**Anti-pattern:**
```python
# DON'T: Hardcoded unique values
library = baker.make(Library, code="music")  # Crashes if another test created "music"
user = baker.make(User, username="host1")    # Crashes if another test created "host1"
```

**Solution:**
```python
import uuid

# DO: Unique values per test
library = baker.make(Library, code=f"music_{uuid.uuid4().hex[:8]}")
user = baker.make(User, username=f"host1_{uuid.uuid4().hex[:8]}")
```

**Files Fixed in T344:**
- api/storage/tests/views/test_file_list.py
- api/storage/tests/views/test_file_retrieve.py
- api/schedule/tests/views/test_show_list.py
- api/schedule/tests/views/test_show_retrieve.py

**Test Isolation Rule:**
Never use hardcoded strings for fields with unique constraints when using `@pytest.mark.django_db(transaction=True)` — transaction rollback may not work perfectly between tests.


## Test Isolation Patterns — T345

**Rule 1: Never use hardcoded values for unique fields**
```python
# BAD - causes UniqueViolation in full suite
user = User.objects.create_user(username="admin_test")

# GOOD - unique per test
import uuid
user = User.objects.create_user(username=f"admin_{uuid.uuid4().hex[:8]}")
```

**Rule 2: Delete related objects before parent (FK constraints)**
```python
# BAD - FK constraint error
Library.objects.all().delete()  # Fails if File references Library

# GOOD - delete in correct order
File.objects.all().delete()
Library.objects.all().delete()
```

**Rule 3: Don't assume auto-increment ID values**
```python
# BAD - assumes no file with ID=123 exists
response = api_client.delete("/api/v2/files/123")
assert response.status_code == 404

# GOOD - use ID that definitely won't exist
response = api_client.delete("/api/v2/files/9999999999999")
assert response.status_code == 404
```

**Files fixed in T345:**
- api/conftest.py — fixture usernames
- api/core/tests/views/test_user.py — test usernames
- api/storage/tests/views/test_library_create.py — cleanup order
- api/storage/tests/views/test_file_delete_not_found.py — ID value
- api/storage/tests/views/test_file_download_404.py — ID value


## MountName Model (T267)

**Location:** `app/api/api/history/models/listener.py`

**Model:**
```python
class MountName(models.Model):
    mount_name = models.CharField(max_length=1024)
    
    class Meta:
        managed = False  # External table (Icecast)
        db_table = "cc_mount_name"
```

**ViewSet:** `MountNameViewSet` in `app/api/api/history/views/listener.py`
- `model_permission_name = "mountname"`
- No owner field (system table for Icecast mount points)

**Permissions:**
- LIST requires 'view_mountname' permission (admin only by default)
- Regular users and guests get 403

**Security notes:**
- No rate limiting observed (potential T666)
- No pagination on LIST (potential T667)
- No input validation on mount_name length beyond DB constraint
