---
# Machine Index
version: 1
schema: knowledge-graph
last_updated: 2026-04-07T12:49:46Z
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
  indexes: []
  relationships:
    - shows have many playlists
    - playlists have many files
    - users own shows/playlists
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
  fixtures:
    - app/api/api/_fixtures/
    - app/playout/tests/conftest.py
  mock_rules:
    - Use pytest-mock for unit tests
    - Use requests-mock for HTTP clients
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
```

# Investigation Log
```yaml
investigation_log: []
```

# Uncertainty Registry
```yaml
unknowns: []
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
single_points_of_failure:
  - component: liquidsoap
    mitigation: Can restart independently
  - component: postgres
    mitigation: Playout caches schedule locally
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
  
  validation_rules:
    - rule: "All repository classes must have entry in class_hierarchy"
      severity: warning
    - rule: "All service dependencies must be in dependency_graph"
      severity: warning
```

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
