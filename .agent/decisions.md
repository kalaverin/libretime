# Decision Log

<!-- Protocol: ~/.config/kimi/skills/decision-protocol/SKILL.md (modified: 2026-04-07T12:03:05Z, commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7) -->
<!-- The following section is a FULL COPY of ~/.config/kimi/skills/decision-protocol/SKILL.md
     Protocol commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7
     Protocol modified: 2026-04-07T12:03:05Z -->
---
name: decision-protocol
description: Protocol for maintaining .agent/decisions.md architectural decision log
---

# Decision Protocol

Architectural Decision Record (ADR) system for tracking decisions, their rationale, and status across AI agent sessions.

## File Structure

```
repo-root/
└── .agent/
    └── decisions.md       # Decision log with status
```

## Read on Session Start

1. **Read .agent/decisions.md** — check for:
   - `ACTIVE` decisions — current constraints/guidelines
   - `PENDING` decisions — awaiting input
   - `SUPERSEDED` decisions — understand history

2. Acknowledge: "Decisions loaded: [X active, Y pending]"

## Decision Lifecycle

### 1. Recording a New Decision

When an architectural/approach decision is made:

```markdown
| YYYY-MM-DDTHH:mm:ssZ | Decision text | Why this choice | ACTIVE | - |
```

Use a **full UTC instant** per `~/.config/kimi/prompts/settings.md` § Timestamps.

Add to the table in chronological order (newest last).

### 2. Save Work / Persist state (this protocol only)

When a **checkpoint** runs (triggers and order: **`~/.config/kimi/templates/agent.md`** or **`.agent/intro.md`** § SKILLS → *Persist state*), this protocol's **sole** responsibility is **`.agent/decisions.md`**.

1. For each **new** architectural or approach decision from this session: add a row to the decision table with **rationale** and status **ACTIVE** (or **PENDING** if blocked).
2. If a decision **supersedes** an older one: mark the old row **SUPERSEDED** and add the replacement row per **§ 4. Superseding Decisions** below.
3. Keep narrative under **Decisions:** in `.agent/history.md` (memory-protocol) aligned with the table — the table is the long-term source of truth.

After finishing this file, continue the checkpoint with **task-protocol**, then **knowledge-protocol**, then **style-protocol**, then **glossary-protocol** (conditional per that skill) if not already done; do not skip **memory-protocol** — it runs first in the template order.

### 3. Pending Decisions

When a decision needs to be made but is blocked:

```markdown
## Pending Decisions

- Use PostgreSQL or MySQL? (raised: 2026-03-25T12:00:00Z, context: Need to evaluate JSON support and performance for our use case)
```

Move to table with status `PENDING` if awaiting external input.

### 4. Superseding Decisions

When a decision changes:

1. Mark old decision:
```markdown
| 2026-03-25T14:00:00Z | ~~Use Redis for sessions~~ | Overkill for MVP | SUPERSEDED | Use in-memory cache |
```

2. Add new decision:
```markdown
| 2026-03-27T09:15:00Z | Use in-memory cache for sessions | Simpler, sufficient for current scale | ACTIVE | - |
```

3. In `.agent/history.md` session, note: "Superseded: [old] → [new]"

## Decision Hygiene Rules

- **Respect .gitignore** — Decisions should not involve modifying files in `.gitignore`
  (except `.agent/` directory). Check .gitignore before making file-related decisions.
- **Every significant decision gets recorded** — if it affects future work, log it
- **Rationale is mandatory** — future you/others need to understand WHY
- **Link related decisions** — use "Superseded By" column
- **Review PENDING regularly** — don't let decisions stall indefinitely
- **Mark stale decisions** — use ~~strikethrough~~ for SUPERSEDED

## What to Record

### Record These
- Technology choices (framework, database, library)
- Architecture patterns (microservices vs monolith, REST vs GraphQL)
- Coding conventions (enforced via this decision)
- Tool choices (linter, formatter, CI/CD)
- Approach choices (sync vs async, eager vs lazy loading)

### Don't Record
- Obvious choices (use git for version control)
- Temporary workarounds with TODOs in code
- Personal preferences without project impact

## Cross-Session Continuity

- Reference ACTIVE decisions when making similar choices
- Check if PENDING decisions are now resolvable
- When questioning a decision, check rationale first

## Example Decision Table

```markdown
| Date | Decision | Rationale | Status | Superseded By |
|------|----------|-----------|--------|---------------|
| 2026-03-20T10:00:00Z | Use FastAPI for API framework | Modern async support, auto-generated docs, type hints | ACTIVE | - |
| 2026-03-22T11:00:00Z | Use SQLAlchemy 2.0 with async | Official async support, type-safe queries | ACTIVE | - |
| 2026-03-25T14:00:00Z | ~~Use raw SQL for complex queries~~ | Hard to maintain, no type safety | SUPERSEDED | Use SQLAlchemy Core |
| 2026-03-27T15:00:00Z | Use SQLAlchemy Core for complex queries | Balance of control and type safety | ACTIVE | - |
| 2026-03-28T16:00:00Z | Use pytest with async fixtures | Standard for FastAPI testing, good async support | ACTIVE | - |
```

## Integration with Session History

When decisions are made in a session, include in `.agent/history.md`:

```markdown
**Decisions:**
- Use PostgreSQL over MySQL (better JSON support for our document storage needs)
- Adopt repository pattern for data access (easier testing, clearer boundaries)
```

These should then be added to `.agent/decisions.md` for long-term tracking.
<!-- END OF PROTOCOL COPY -->

| Date | Decision | Rationale | Status | Superseded By |
|------|----------|-----------|--------|---------------|
| 2026-04-07T16:28:44Z | ~~Use `.replace(tzinfo=None)` for datetime comparisons in API tests~~ | API returns naive ISO datetimes, model_bakery creates timezone-aware fields; normalization done in test assertions | SUPERSEDED | Use timezone-aware datetime with Z format |
| 2026-04-07T16:28:44Z | ~~Set `USE_TZ = False` in test settings~~ | Avoids Django 5.0 deprecation warning while keeping test compatibility | SUPERSEDED | Use USE_TZ=True with DATETIME_FORMAT |
| 2026-04-09T11:51:00Z | Set `USE_TZ = True` in test settings with `DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"` | API must return UTC datetimes with Z suffix; aligns test env with production | ACTIVE | - |
| 2026-04-09T11:51:00Z | Use `sdk.format_datetime()` for datetime-to-string conversion | Ensures consistent Z-formatted UTC datetime strings across codebase | ACTIVE | - |
| 2026-04-09T11:51:00Z | Use `now_seconds()` helper in tests | model_bakery creates microsecond-precision datetimes; DRF serializes seconds only; zero microseconds for consistent assertions | ACTIVE | - |
| 2026-04-09T14:41:24Z | Use `@pytest.mark.xfail` to document production bugs in tests | Tests should document current behavior including bugs; xfail with reason="BUG T<n>: description" creates regression test that passes when bug is fixed | ACTIVE | - |
| 2026-04-09T14:41:24Z | Create T<n> bug entries in tasks.md for each documented bug | Centralized bug tracking with unique IDs (T316, T317, T318) enables cross-referencing in tests, decisions, and history | ACTIVE | - |
| 2026-04-10T22:08:00Z | Use `credentials()` not `defaults[]` to override DRF APIClient auth | `credentials()` has priority over `defaults[]` in DRF APIClient; `defaults[auth]` does not override `credentials(auth)` | ACTIVE | - |
| 2026-04-10T22:50:00Z | Document Authorization header case sensitivity as known bug | RFC 7230 violation but low impact; use `@pytest.mark.xfail` to track; fix when auth system refactored | ACTIVE | - |
| 2026-04-10T23:00:00Z | Standardize BOLA fix pattern across all ViewSets | Show/Webstream pattern (check_authorization_header + ownership filter) is the reference implementation; apply to Playlist, SmartBlock, File | ACTIVE | - |
| 2026-04-10T23:35:00Z | Document complete permissions system | Full inventory in .agent/research/permissions_inventory.md and permissions_matrix.md; use as reference for all permission-related work | ACTIVE | - |
| 2026-04-11T03:00:00Z | Centralize security validators in `api/validators/` | Single location for path traversal, SSRF, XSS validation; promotes reuse and consistent security posture | ACTIVE | - |
| 2026-04-11T03:00:00Z | Use regex-based XSS detection at API boundary | Block XSS payloads in serializers, not template layer; fail-fast with 400 error | ACTIVE | - |
| 2026-04-11T03:00:00Z | Use SecureModelSerializer as base for all model serializers | Built-in mass assignment protection (id, owner, timestamps blocked); consistent security across API | ACTIVE | - |

<!--
Format:
| YYYY-MM-DDTHH:mm:ssZ | Decision text | Why this choice | ACTIVE/SUPERSEDED/PENDING | (if superseded) |
-->

## Pending Decisions

<!--
Decisions that need to be made:
- Question? (raised: YYYY-MM-DDTHH:mm:ssZ, context: link or brief description)
-->

## Decision Templates

When superseding a decision:
1. Mark old decision as SUPERSEDED
2. Add link to new decision in "Superseded By"
3. Add new decision row with ACTIVE status

Example:
```markdown
| 2026-03-25T14:30:00Z | ~~Use Redis for sessions~~ | Overkill for MVP | SUPERSEDED | Use in-memory cache |
| 2026-03-27T09:15:00Z | Use in-memory cache for sessions | Simpler, sufficient for current scale | ACTIVE | - |
```
