---
# Machine Index
version: 1
schema: knowledge-graph
last_updated: 2026-04-06T16:54:33Z
graph_hash: ""
---

<!-- Protocol: ~/.config/kimi/skills/knowledge-protocol/SKILL.md (modified: 2026-04-03T19:39:37Z, commit: d7b218d442ccc2d8229bbc567649af803b333b28) -->
<!-- The following section is a FULL COPY of the protocol above, auto-updated on init/sync. Do not edit manually. -->
---
name: knowledge-protocol
description: Protocol for maintaining .agent/knowledge.md - machine-readable accumulated knowledge about codebase
---

# Knowledge Protocol

Machine-readable knowledge base for AI agents. Unlike history.md (chronological sessions), 
this file contains accumulated facts, patterns, and insights discovered during work.

**Hub settings:** `~/.config/kimi/prompts/settings.md` — read **in full** before heavy edits; **supreme** — **nothing** overrides it.

## File Structure

```
repo-root/
└── .agent/
    └── knowledge.md       # Accumulated codebase knowledge
```

## Core Principle

**NEVER STOP WRITING. Knowledge.md grows continuously or it's useless.**

Unlike history.md (updated once per session), knowledge.md is updated CONSTANTLY — 
after every grep, every discussion, every discovered connection. Default action: WRITE.

### Autonomous updates (no user request)

The agent updates **knowledge.md on its own**. The user does **not** need to say "remember this", "add to knowledge", or wait for explicit "save work". Deferring writes until a checkpoint or until the user asks is **wrong** — checkpoints **reconcile** knowledge they might have missed; they do not replace continuous capture. **Disk prose:** `~/.config/kimi/prompts/settings.md` § **On-disk language**.

### The "Puffy Knowledge Base" Rule

If knowledge.md is not growing during your session, you are doing it wrong.
Every 10 minutes of work = at least one new entry. Minimum.

## Read on Session Start

1. **Read .agent/knowledge.md entirely** - it's optimized for machine parsing
2. **Parse YAML blocks** - restore mental model of:
   - Dependency graph
   - Class hierarchies
   - Data flows
   - Known gotchas
   - Investigation results
3. **Acknowledge**: "Knowledge loaded: X components, Y gotchas, Z investigations"

## Write Triggers (MANDATORY - NO EXCEPTIONS)

**ALWAYS WRITE KNOWLEDGE.md. NO EXCEPTIONS.**

You are FORBIDDEN from "remembering for later". Write immediately or lose forever.

### Immediate Write Required (Do Not Pass Go)

These trigger INSTANT knowledge.md update — stop what you're doing and write:

| Trigger | Action | Example |
|---------|--------|---------|
| Finished grep/search | Add pattern to insights | "Found 12 files using X pattern" |
| Discussion with user | Add conclusion to insights | "User clarified Y behavior" |
| Found bug/gotcha | Add to gotchas | "Z fails when condition W" |
| Read new file | Update dependency_graph | "Service X calls Y" |
| Traced data flow | Update data_flow | "Request flows A→B→C" |
| Fixed something | Update investigation_log | "Root cause was X" |
| User explained domain | Add to insights | "Business rule: ..." |
| Saw unexpected pattern | Add to insights | "Interesting: X does Y" |
| Any "aha!" moment | WRITE IT DOWN | Immediately. Now.

### 1. Component Relationships
- New service/repository/controller created
- New dependency between components discovered
- Interface/abstract class found

→ Update: `dependency_graph` YAML block

### 2. Class Hierarchy Changes
- Inheritance chain discovered
- Mixin pattern found
- Interface implementation

→ Update: `class_hierarchy` YAML block

### 3. Data Flow Discovery
- Request flows through multiple layers
- Background job processing
- Event handling

→ Update: `data_flow` YAML block

### 4. Database Knowledge
- Table structure understood
- Index usage discovered
- Relationship cardinality found
- Query pattern analyzed

→ Update: `database` YAML block

### 5. Gotchas Found
- Non-obvious behavior
- Environment-specific quirks
- Counter-intuitive patterns
- Hidden dependencies

→ Update: `gotchas` YAML block

### 6. Random Insights
- Unexpected connections between components
- Performance characteristics
- Security implications
- Design patterns in use

→ Update: `insights` YAML block

### 7. Investigation Results
- Debug session concluded
- Root cause found
- Experiment completed

→ Update: `investigation_log` YAML block

## YAML Schema

### dependency_graph
```yaml
dependency_graph:
  components:
    component_name:
      type: [service|repository|router|model|utility]
      path: file_path
      depends_on: [list_of_components]
      provides: [list_of_capabilities]
      critical: true|false
  
  edges:
    - from: component_a
      to: component_b
      type: [sync|async|event|db_query]
      notes: "optional details"
```

### class_hierarchy
```yaml
class_hierarchy:
  classes:
    ClassName:
      extends: ParentClass
      mixins: [Mixin1, Mixin2]
      implements: [Interface1]
      abstract: true|false
      file: path/to/file.py
      methods: [method1, method2]
      
  interfaces:
    InterfaceName:
      methods: [method1, method2]
      implementors: [ClassA, ClassB]
```

### data_flow
(Top-level key **`data_flow`** in `templates/knowledge.md` — not `data_flow_map`.)

```yaml
data_flow:
  flows: {}
```

### database
(Top-level key **`database`** — not `database_schema_knowledge`.)

```yaml
database:
  tables: {}
  indexes: []
  relationships: []
```

### third_party
(Top-level key **`third_party`** for external packages/services — not `external_dependencies`.)

```yaml
third_party: {}
```

### gotchas
```yaml
gotchas:
  - id: unique_id
    severity: [critical|high|medium|low]
    category: [behavior|performance|security|environment]
    title: "Short description"
    description: "Detailed explanation"
    location: "Where it occurs"
    workaround: "How to handle it"
    discovered: "YYYY-MM-DDTHH:mm:ssZ"
    discovered_in: "Session context"
```

### insights
```yaml
insights:
  - id: insight_001
    type: [pattern|connection|performance|security|design]
    title: "Brief description"
    description: "Detailed insight"
    relates_to: [component_a, component_b]
    confidence: [confirmed|likely|speculative]
    discovered: "YYYY-MM-DDTHH:mm:ssZ"
```

### investigation_log
```yaml
investigation_log:
  - id: INV-001
    topic: "What was investigated"
    status: [ongoing|resolved|stalled]
    conclusion: "What was learned"
    root_cause: "If resolved"
    solution: "How fixed"
    files_involved: [path1, path2]
    discovered: "YYYY-MM-DDTHH:mm:ssZ"
    resolved: "YYYY-MM-DDTHH:mm:ssZ"
```

## Auto-Update Rules (for repo-update)

repo-update agent MUST scan code and update knowledge.md:

### Triggers
```yaml
auto_update_triggers:
  new_model:
    pattern: "**/models/*.py"
    action: "Add to database"
    
  new_repository:
    pattern: "**/repositories/*.py"
    action: "Add to class_hierarchy and dependency_graph"
    
  new_service:
    pattern: "**/services/*.py"
    action: "Add to dependency_graph, map dependencies"
    
  new_router:
    pattern: "**/routers/*.py"
    action: "Add to data_flow"
    
  requirements_changed:
    pattern: "requirements*.txt"
    action: "Update third_party"
```

### Validation
```yaml
validation_rules:
  - rule: "All classes in inheritance chain must be documented"
    check: class_hierarchy
    severity: warning
    
  - rule: "All database models must have schema entry"
    check: database
    severity: error
    
  - rule: "Gotchas must have severity and workaround"
    check: gotchas
    severity: error
```

## Save Work / Persist state (this protocol only)

When a **checkpoint** runs (triggers and order: **`~/.config/kimi/templates/agent.md`** or **`.agent/intro.md`** § SKILLS → *Persist state*), this protocol's **sole** responsibility is **`.agent/knowledge.md`**. Continuous autonomous updates should already be happening; this step is a **flush / reconcile**, not the first time you write.

1. **Flush** anything learned this session that is not yet recorded — use the right YAML blocks per **Write Triggers** and **YAML Schema** (`gotchas`, `insights`, `investigation_log`, `dependency_graph`, etc.).
2. If the session was **non-trivial** but everything is already captured from continuous writes, do a quick verification pass; if still nothing to add, add a minimal **insight** noting "checkpoint, no new durable facts."

Finish **memory-protocol**, **decision-protocol**, and **task-protocol** before this step when following the template order; **style-protocol** then **glossary-protocol** (conditional) run **after** this step.

## Example Entries

### Gotcha Example
```yaml
gotchas:
  - id: gotcha_001
    severity: high
    category: behavior
    title: "FastAPI dependency caching"
    description: |
      FastAPI caches dependency results per request by default.
      If dependency returns mutable object (list, dict), 
      modifications persist across subsequent calls in same request.
    location: "All FastAPI dependencies"
    workaround: "Return immutable objects or copy before returning"
    discovered: "2026-04-03T12:00:00Z"
    discovered_in: "Debugging why user permissions accumulated"
```

### Insight Example
```yaml
insights:
  - id: insight_003
    type: connection
    title: "Auth service bypasses cache for admin users"
    description: |
      Admin user authentication always hits database, never cache.
      This is intentional (security) but not documented.
      Found by noticing cache miss pattern in logs.
    relates_to: [auth_service, redis_cache]
    confidence: confirmed
    discovered: "2026-04-03T12:00:00Z"
```

### Investigation Example
```yaml
investigation_log:
  - id: INV-005
    topic: "Why user sessions expire early?"
    status: resolved
    conclusion: "Timezone mismatch between app and Redis"
    root_cause: "App uses UTC, Redis uses system time (EST)"
    solution: "Force Redis to UTC in config, added tz check on startup"
    files_involved: 
      - app/core/config.py
      - app/services/session.py
      - docker-compose.yml
    discovered: "2026-04-01"
    resolved: "2026-04-02"
```

## Hygiene Rules (ENFORCED)

### The Golden Rule
**If you thought it, write it. If you found it, log it. If you discussed it, document it.**

### Mandatory Actions
- **Write IMMEDIATELY** — stop mid-sentence if needed. No batching. No "later".
- **Every grep → insight** — search results are knowledge. Log patterns found.
- **Every discussion → entry** — user explanations are gold. Document domain knowledge.
- **Every debug → investigation_log** — even if unresolved. ESPECIALLY if unresolved.
- **Every fix → conclusion** — root cause must be recorded for posterity.

### Volume Requirements
- Minimum: 1 entry per 10 minutes of active work
- Target: Knowledge.md should grow by 10-50 lines per hour of work
- Success metric: File size increases every session

### Quality Rules
- **Use IDs** — every entry must have unique ID for referencing
- **Be specific** — file paths, line numbers, exact error messages
- **Link related entries** — use relates_to, references fields  
- **Mark confidence** — distinguish confirmed facts from speculation
- **Respect .gitignore** — Never scan files in `.gitignore` (except `.agent/`)

### Anti-Patterns (FORBIDDEN)
- ❌ "I'll add this to knowledge.md at the end"
- ❌ "This is too small to document"
- ❌ "I already remember this"
- ❌ "I'll batch these updates"
- ❌ "This is obvious"
- ❌ Waiting for the user to say "remember" or "save" before writing durable facts

## Cross-References to Other Files

- `.agent/history.md` - links to investigation sessions
- `.agent/decisions.md` - architectural decisions that explain why
- Root `AGENTS.md` (symlink → `.agent/intro.md`) — links to external resources

## Format

knowledge.md uses hybrid format:
- Markdown headers for sections
- YAML blocks for structured data
- Free text only in descriptions

This allows both human reading and machine parsing.
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
