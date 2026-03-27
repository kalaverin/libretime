# libretime — Agent Context

- This file modification datetime: 2026-03-27
- File modified at commit: 6205e003a371d3a7bd234daceccbaae69a2bb200

## PROJECT_CONTEXT
- Stack: Python, Django REST Framework, Celery, RabbitMQ, PostgreSQL, Liquidsoap
- Language version: Python >=3.10, <3.12
- Framework: Django 4.2 (API), Zend Framework 1 (Legacy PHP)
- Entry points:
  - API: `api.manage:main` (Django management)
  - Playout: `playout.main:cli`, `playout.liquidsoap.main:cli`, `playout.notify:cli`
  - Analyzer: `analyzer.main:cli`
  - Worker: `worker.main:cli`
- Build: `make install` (mise tools), `uv sync --all-packages --group development` (deps)
- Test runner: `pytest` / `pytest-django` (run from component directory)
- Lint: `make lint` or `uv run pre-commit run --config etc/pre-commit.yaml --all`
- Format: black (line length 79, Python 3.10 target) via pre-commit

## ARCHITECTURE

Monolithic radio broadcast automation system split into two functional blocks:

### Create Schedule (Content Management)
| Component | Path | Purpose |
|-----------|------|---------|
| `api` | `app/api/` | Django REST API, database models, business logic |
| `worker` | `app/worker/` | Celery worker for async tasks (podcasts, notifications) |
| `analyzer` | `app/analyzer/` | Audio file analysis (metadata, replaygain, cuepoints) |
| Legacy Web | `legacy/` | PHP web UI (Zend Framework 1) |

### Play Schedule (Audio Playout)
| Component | Path | Purpose |
|-----------|------|---------|
| `playout` | `app/playout/` | Playout engine, schedule execution, Liquidsoap control |
| Liquidsoap | External | Audio streaming/processing engine |
| Icecast/HLS | External | Audio streaming servers |

### Shared Libraries
| Component | Path | Purpose |
|-----------|------|---------|
| `sdk` | `src/sdk/` | Shared utilities (config, logging, HTTP client, datetime) |

### API Django Apps (`app/api/api/`)
- `core` - users, auth, preferences, workers
- `storage` - files, libraries
- `schedule` - shows, playlists, smart blocks, webstreams
- `podcasts` - podcast management
- `history` - listener stats, playout history
- `legacy` - migrations from old schema

## CONVENTIONS

### Code Style
- Line length: 79 characters
- Type hints required (Python 3.10+)
- Import order: future → stdlib → third-party → first-party → local (enforced by ruff)

### Commits
- Follow [Conventional Commits](https://www.conventionalcommits.org/)
- Prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

### Development Process
- Based on [C4 process](https://rfc.zeromq.org/spec:42/c4/)
- Main branch: `main`
- Stable branches: `stable-X.Y`

### Pre-commit Hooks (etc/pre-commit.yaml)
- uv lock check, yamlfix, yamllint
- black (formatting), ruff (linting)
- mypy, basedpyright (type checking)
- refurb (bad patterns), vulture (unused code)
- bandit, hexora (security)
- codespell (spelling)

### Testing
- Run tests from component directory: `cd app/<component> && uv run pytest`
- Django tests use `pytest-django` with `DJANGO_SETTINGS_MODULE=api.settings.testing`

## AGENT_RULES
- Never modify files outside app/, src/ and tests/ without explicit confirmation
- Do not run tests or linters without explicit request
- Do not refactor code without explicit request
- Use git only for read operations, never for write operations (e.g. commit, push, pull) without explicit request
- When in doubt, check .agent/decisions.md for active decisions
- Update .agent/tasks.md when starting/completing work items

## MEMORY_HINTS
- Workspace uses `uv` for package management (not pip/poetry)
- Each app/* component is a separate package with its own pyproject.toml
- Legacy PHP code in `legacy/` should rarely be modified
- Services communicate via RabbitMQ message queue
- Playout can operate independently if API is down (schedule is cached)
- Not designed for multi-tenancy - one install per radio station

## KNOWN_ISSUES
- Legacy codebase contains technical debt (Zend Framework 1, Propel ORM)
- Some tests may require Docker services (postgres, rabbitmq)
- Liquidsoap integration requires external binary

## EXTERNAL RESOURCES
- Documentation: https://libretime.org/docs/
- Forum: https://discourse.libretime.org
- Matrix: #libretime:matrix.org
- C4 Process: https://rfc.zeromq.org/spec:42/c4/
- Conventional Commits: https://www.conventionalcommits.org/

---

*This file is maintained by repo-init-agent. Last full sync: 2026-03-27*
