# Work History — 2026-04-06T16:54:33Z

<!-- Protocol: ~/.config/kimi/skills/memory-protocol/SKILL.md (modified: 2026-04-03T19:39:37Z, commit: d7b218d442ccc2d8229bbc567649af803b333b28) -->
<!-- The following section is a FULL COPY of the protocol above, auto-updated on init/sync. Do not edit manually. -->
---
name: memory-protocol
description: Protocol for maintaining .agent/history.md session logs and cross-session continuity
---

# Memory Protocol

Cross-session memory system for AI agents working on long-running projects.

## File Structure

```
repo-root/
├── AGENTS.md              # repo root: symlink → .agent/intro.md (canonical; not reverse)
└── .agent/
    ├── decisions.md       # Decision log with status
    ├── history.md         # Work history (append-only)
    ├── style.md           # Empirical code-style ledger (S<n>)
    ├── glossary.md        # User-defined terms → model meaning (G<n>)
    └── tasks.md           # Current and queued tasks
```

## Related Protocols

- **Hub settings** — `~/.config/kimi/prompts/settings.md`: read **in full** before this protocol in hub-driven work; **supreme** — **nothing** overrides it. Session bodies you append: **§ On-disk language** (English telegraphic).
- **task-protocol** — How to manage .agent/tasks.md
- **style-protocol** — How to maintain .agent/style.md
- **glossary-protocol** — How to maintain .agent/glossary.md
- **decision-protocol** — How to maintain .agent/decisions.md
- **knowledge-protocol** — How to maintain .agent/knowledge.md

## Read on Session Start

1. **Read `AGENTS.md` at repo root** or **`.agent/intro.md`** (same file; root entry is symlink → intro) — understand project context
2. **Read .gitignore** — note all ignored files/patterns (always ignore these, except `.agent/`)
3. **Smart read .agent/history.md** — see below for efficient reading
4. **Read .agent/tasks.md** — check active/queued tasks (see task-protocol)
5. **Read .agent/decisions.md** — understand active decisions (see decision-protocol)
6. Acknowledge: "Memory loaded: [N sessions, last session header, X active tasks]" — headers use UTC `Z` per `~/.config/kimi/prompts/settings.md` § Timestamps

## Smart Memory Reading

To avoid loading excessive context:

1. **Always read** first 50 lines (initialization + project summary)
2. **Read last 5 sessions** fully
3. **For older sessions** — read only:
   - Session header (date/time)
   - **Completed** section (brief)
   - **Decisions** section (with status)
   - Skip detailed discoveries and file lists
4. **Skip entirely** sessions marked with `[ARCHIVED]` in header

## Write on Session End (or after non-trivial task)

Also run this append at every **Persist state** checkpoint (explicit save, pivot phrases, or non-trivial work done — full list under **`~/.config/kimi/templates/agent.md`** or **`.agent/intro.md`** § SKILLS → *Persist state*). Same checkpoint order: **history → decisions → tasks → knowledge**; this protocol is **first**.

**Append at the END of Sessions section** (before `## Archive` or before the 
`<!-- Agent appends new sessions -->` comment):

Session headers MUST follow **Timestamps** in `~/.config/kimi/prompts/settings.md` (`YYYY-MM-DDTHH:mm:ssZ`), e.g. `### [2026-04-03T19:41:14Z]`.

```markdown
### [YYYY-MM-DDTHH:mm:ssZ]
**Completed:** <what was actually done>
**Discovered:** <non-obvious findings, gotchas, env quirks>
**Decisions:** <architectural/approach decisions made and why>
**Open:** <unresolved questions, blocked items>
**Modified files:** <list of changed files>
```

**Order:** Sessions are stored chronologically from OLDEST to NEWEST (new sessions 
added at the END of the Sessions section).

## Important Rules

- **Respect .gitignore** — Never read, modify, or suggest changes to files listed in 
  `.gitignore`, except `.agent/` directory which must always be tracked and maintained
- **Never overwrite** existing entries in history.md — append only
- **Auto-archive**: If .agent/history.md exceeds 200 lines, move old sessions to Archive

## Save Work / Persist state (this protocol only)

When a **checkpoint** runs (triggers and order: **`~/.config/kimi/templates/agent.md`** or **`.agent/intro.md`** § SKILLS → *Persist state*), this protocol's **sole** responsibility is **`.agent/history.md`**.

1. Follow **Write on Session End (or after non-trivial task)** above: append **one** new session entry at the end of `## Sessions`.
2. In the entry's **Decisions:** lines, summarize outcomes at **session** level only. Full ADR rows and statuses belong in **decision-protocol** during the same checkpoint, not duplicated as prose here.

After finishing this file, continue the same checkpoint with **decision-protocol**, then **task-protocol**, then **knowledge-protocol**, then **style-protocol**, then **glossary-protocol** (the latter only when its **Write gate** applied — see that skill) — do not stop early.

## Memory Hygiene Rules

- **Never overwrite** existing entries — append only
- **Auto-archive**: If .agent/history.md exceeds 200 lines:
  1. Create `## Archive` section at end if not exists
  2. Move sessions older than 10 most recent to Archive
  3. Summarize archived session to 3-4 lines max
- **Stale marking**: Mark superseded decisions with ~~strikethrough~~
- **Do NOT store**: temp debug output, trivial one-liners, obvious facts
- **Do store**: non-obvious findings, architectural decisions, gotchas

## Session Summary (Auto-Generated)

Every 10 sessions, prepend to .agent/history.md:

```markdown
## Session Summary (as of YYYY-MM-DDTHH:mm:ssZ)
- **Total sessions:** 47
- **Active decisions:** 5
- **Last focus:** API refactoring
- **Key patterns:** FastAPI, SQLAlchemy, pytest
- **Common gotchas:**
  - Database needs re-creation between tests
```

## Cross-Session Continuity

- If task was interrupted: mark in `.agent/tasks.md` as `[INTERRUPTED]` with last known state (see task-protocol)
- On resume: read `[INTERRUPTED]` tasks first, restore context before accepting new tasks

## Example Session Entry

```markdown
### [2026-03-27T14:30:00Z]
**Completed:**
- Implemented user authentication middleware
- Added JWT token validation
- Created login/logout endpoints

**Discovered:**
- FastAPI dependency injection requires `Depends()` on every protected route
- The test database needs to be re-created between test runs (no rollback support)

**Decisions:**
- Use `python-jose` instead of `PyJWT` for better algorithm support
- Store refresh tokens in Redis with 7-day TTL

**Open:**
- How to handle token refresh in WebSocket connections?
- Rate limiting strategy for login attempts

**Modified files:**
- `app/auth/middleware.py`
- `app/auth/router.py`
- `tests/test_auth.py`
```
<!-- END OF PROTOCOL COPY -->

You MUST append a session entry after completing any work

## Initialization
- Repo scaffolded: 2026-04-06T16:28:17Z
- Current commit: 773e4c98e93e640c66136f2d532e42a8641d50e5
- `.agent/intro.md`: created (root `AGENTS.md` → symlink here)
- Initialized by: repo-init-agent

## Session Summary
<!-- Generated every 10 sessions -->
- Total sessions: 1
- Active decisions: 0
- Last focus: Repository initialization (MIGRATION from agent.old)
- Key patterns: Monolithic architecture with clear separation between "create schedule" and "play schedule"

## Sessions

### [2026-04-06T16:28:17Z]
**Completed:**
- Repository re-initialized with canonical .agent/ structure
- `.agent/intro.md` created (canonical) + root `AGENTS.md` → symlink to it
- `.agent/history.md` created with work history
- `.agent/tasks.md` updated with task tracking (migrated from agent.old)
- `.agent/decisions.md` updated with decision log (migrated from agent.old)
- `.agent/knowledge.md` created with initial codebase knowledge
- `.agent/style.md` created with style ledger
- `.agent/glossary.md` created with glossary structure
- Migrated data from `agent.old/` directory:
  - Imported 1 session from `agent.old/MEMORY.md`
  - Merged tasks from agent.old context
  - Merged decisions from agent.old context

**Discovered:**
- Multi-component Python workspace using uv (not poetry/pip)
- Django REST API with Celery workers for async processing
- Legacy PHP codebase in `legacy/` directory (Zend Framework 1)
- Audio playout handled by Liquidsoap integration
- Strong separation: "create schedule" vs "play schedule" blocks
- Pre-commit hooks heavily customized with many quality checks
- UV workspace with members: `app/*`, `src/*`

**Decisions:**
- Migrated from agent.old structure to canonical .agent/ layout
- Root AGENTS.md is now a symlink to .agent/intro.md (not standalone)

**Open:**
- None

**Modified files:**
- `.agent/intro.md` — created canonical project context
- `AGENTS.md` — created symlink to .agent/intro.md
- `.agent/history.md` — created work history
- `.agent/tasks.md` — created task tracking
- `.agent/decisions.md` — created decision log
- `.agent/knowledge.md` — created knowledge base
- `.agent/style.md` — created style ledger
- `.agent/glossary.md` — created glossary

<!-- Agent appends new sessions HERE, at the END of Sessions section, before the --- separator -->
<!-- Format:
### [YYYY-MM-DDTHH:mm:ssZ]
**Completed:** <what was actually done>
**Discovered:** <non-obvious findings, gotchas, env quirks>
**Decisions:** <architectural/approach decisions made and why>
**Open:** <unresolved questions, blocked items>
**Modified files:** <list of changed files>
-->

---

## Archive
<!-- Old sessions summarized here when history.md exceeds 200 lines -->
