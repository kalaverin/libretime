# LibreTime - Agent Guide

**Version:** 4.5.0  
**Commit:** f6e3015e8  
**License:** AGPLv3  
**Python:** >=3.10, <3.12

---

## Overview

LibreTime is a radio broadcast automation system - a community-managed fork of the AirTime project. It enables running online or terrestrial radio stations with scheduling, playout, and streaming capabilities.

---

## Architecture

The system is split into two main monolithic blocks:

### 1. Create the Schedule
Components for content management and scheduling:
- **Web API** (Django REST Framework) - core backend
- **Worker** (Celery) - background task processing
- **Message API** - communication layer
- **Web App** - Legacy PHP interface

### 2. Play the Schedule
Components for audio playout and streaming:
- **Playout** - schedule execution engine
- **Liquidsoap** - audio streaming/processing engine
- **Icecast** - traditional audio streaming server
- **HLS** - modern HTTP Live Streaming

```
┌─────────────────────────────────────────────────────────────┐
│                     Create Schedule                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Web App │  │   API   │  │ Worker  │  │ Message │        │
│  │  (PHP)  │──│ (Django)│  │(Celery) │  │   API   │        │
│  └─────────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
└────────────────────┼────────────┼────────────┼──────────────┘
                     │            │            │
                     ▼            ▼            ▼
              ┌─────────┐  ┌─────────┐  ┌──────────────┐
              │Database │  │Storage  │  │Message Queue │
              │(PostgreSQL)         │  │(RabbitMQ)    │
              └─────────┘  └─────────┘  └──────────────┘
                     ▲                           ▲
                     │                           │
┌────────────────────┼───────────────────────────┼──────────────┐
│                     │      Play Schedule        │              │
│  ┌─────────┐  ┌────┴────┐                     │              │
│  │Playout  │──│Liquidsoap                      │              │
│  │(Python) │  │         │◄────────────────────┘              │
│  └─────────┘  └────┬────┘                                    │
│                    │                                         │
│              ┌─────┴─────┐                                   │
│              ▼           ▼                                   │
│        ┌─────────┐  ┌─────────┐                              │
│        │ Icecast │  │   HLS   │                              │
│        └─────────┘  └─────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Workspace Structure

### `app/*` - Applications

| Component | Language | Purpose |
|-----------|----------|---------|
| `analyzer/` | Python | Audio file analysis (metadata, replaygain, cuepoints, playability) |
| `api/` | Python (Django) | REST API, database models, business logic |
| `api-client/` | Python | HTTP client library for API communication |
| `playout/` | Python | Playout engine, Liquidsoap integration, scheduling |
| `worker/` | Python | Celery worker for async tasks (podcasts, notifications) |

### `src/*` - Libraries

| Component | Language | Purpose |
|-----------|----------|---------|
| `sdk/` | Python | Shared utilities (config, logging, HTTP client, datetime helpers) |

### `legacy/` - Legacy Application

| Component | Language | Purpose |
|-----------|----------|---------|
| `application/` | PHP (Zend FW 1) | Web UI, controllers, models (Propel ORM) |
| `public/` | PHP/CSS/JS | Static assets, entry point |
| `locale/` | PO files | Internationalization (15+ languages) |

---

## Component Details

### analyzer
- **Entry point:** `analyzer.main:cli`
- **Queue:** Listens to RabbitMQ for file analysis jobs
- **Pipeline stages:**
  1. `analyze_metadata` - extract ID3/metadata
  2. `analyze_replaygain` - loudness normalization data
  3. `analyze_cuepoint` - silence detection
  4. `analyze_playability` - validate file can be played
  5. `organise_file` - move to storage

### api
- **Entry point:** `api.manage:main`
- **Django apps:**
  - `core` - users, auth, preferences, workers
  - `storage` - files, libraries
  - `schedule` - shows, playlists, smart blocks, webstreams
  - `podcasts` - podcast management
  - `history` - listener stats, playout history
  - `legacy` - migrations from old schema

### playout
- **Entry points:** 
  - `playout.main:cli` - main playout daemon
  - `playout.liquidsoap.main:cli` - Liquidsoap control
  - `playout.notify.main:cli` - notification handler
- **Key modules:**
  - `player/` - schedule fetching, event queue, file management
  - `liquidsoap/` - Liquidsoap integration (telnet/socket control)
  - `history/` - playout statistics

### worker
- **Entry point:** `worker.main:cli`
- **Tasks:**
  - Podcast downloading
  - Email notifications
  - Background processing

### sdk
- **Modules:**
  - `config/` - configuration parsing (env-based, pydantic models)
  - `http/` - HTTP client with retry logic
  - `logging.py` - structured logging setup
  - `datetime.py` - timezone utilities

---

## Development Toolchain

### Package Management
- **uv** - Modern Python package manager and workspace tool
- Workspace defined in root `pyproject.toml` with members: `app/*`, `src/*`

### Task Runner
- **just** - Command runner (see `justfile`)
  - `just` - list commands
  - `just develop` - run development environment
  - `just upgrade` - upgrade all dependencies
  - `just clean` - clean cache files
  - `just dock` - build Docker image

### Environment Management
- **mise** - Tool version manager (see `mise.toml`)
- Install: `make install`

### Linting & Formatting
- **ruff** - Fast Python linter/formatter (config in `etc/lint/ruff.toml`)
  - Line length: 79
  - Target: Python 3.10
- **mypy/basedpyright** - Type checking
- **pre-commit** - Git hooks for quality checks (config: `etc/pre-commit.yaml`)

### Testing
- **pytest** - Test runner
- **pytest-django** - Django testing utilities
- Run: `uv run pytest` from component directory

---

## Code Conventions

### Commits
- Follow [Conventional Commits](https://www.conventionalcommits.org/)
- Examples: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

### Development Process
- Based on [C4 development process](https://rfc.zeromq.org/spec:42/c4/)
- Main branch: `main`
- Stable branches: `stable-X.Y`

### Python Style
- Type hints required (Python 3.10+)
- Black-compatible formatting via ruff
- Import order: future, stdlib, third-party, first-party, local

---

## Common Tasks

### Setup Development Environment
```bash
make install        # Install mise tools
uv sync --all-packages --group development  # Install deps
pre-commit install  # Setup git hooks
```

### Run Development Stack
```bash
just develop
# or with Docker:
make dev
```

### Run Linters
```bash
make lint
# or directly:
uv run pre-commit run --config etc/pre-commit.yaml --all
```

### Type Check
```bash
uv run basedpyright
uv run basedmypy
```

### Run Tests
```bash
cd app/<component>
uv run pytest
```

### Update Dependencies
```bash
just upgrade
```

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Root workspace, deps, tool configs |
| `justfile` | Task definitions |
| `mise.toml` | Tool versions |
| `etc/lint/ruff.toml` | Linter rules |
| `etc/pre-commit.yaml` | Pre-commit hooks |
| `docker-compose.yml` | Local development stack |
| `app/*/pyproject.toml` | Component-specific deps |

---

## External Services

| Service | Usage | Config |
|---------|-------|--------|
| PostgreSQL | Database | `DATABASE_URL` |
| RabbitMQ | Message queue | `RABBITMQ_*` |
| Icecast | Audio streaming | Stream settings in DB |
| Liquidsoap | Audio engine | Generated config |
| Redis | Celery backend | `REDIS_*` |

---

## Documentation

- User docs: `docs/user-manual/`
- Admin docs: `docs/admin-manual/`
- Developer docs: `docs/developer-manual/`
- Architecture: `docs/contributor-manual/design/architecture.md`

---

## Notes

- Each component has its own `Makefile` and `README.md`
- Services communicate via RabbitMQ message queue
- Strong separation between "Create schedule" and "Play schedule" blocks
- Playout can operate independently if API is down (schedule cached)
- Not designed for multi-tenancy - one install per radio station
