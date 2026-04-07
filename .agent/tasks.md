# Active Tasks

<!-- Protocol: ~/.config/kimi/skills/task-protocol/SKILL.md (modified: 2026-04-05T02:38:33Z, commit: 78920ccbaab368bbbd6edb32109fbe10f153df45) -->
<!-- The following section is a FULL COPY of the protocol above, auto-updated on init/sync. Do not edit manually. -->
---
name: task-protocol
description: Protocol for maintaining .agent/tasks.md task tracking and work item management
---

# Task Protocol

Task tracking system for managing active, blocked, and completed work items across AI agent sessions.

**Hub settings:** `~/.config/kimi/prompts/settings.md` — in hub-driven work, read **in full** first; **supreme** — **nothing** overrides it. Date/time fields follow § Timestamps; task prose § On-disk language.

## Task identity (scope + global ID)

Every task has:

- **`scope`** — one English word, **lowercase**, Latin alphabet only: the *kind* of work (feature, bugfix, chore, audit, …).
- **`T<n>`** — **global** task identifier: literal **`T`** plus a decimal integer **`n`** with **no leading zeros** (`T1`, `T12`, `T1042`). **One sequence per repository:** backlog, active, completed, and cancelled entries all share the same counter. **`n` never decreases and is never reused** (cancelled tasks keep their `T<n>` in the file).

**Canonical heading (H2):**

```markdown
## [PRIORITY] <scope> T<n> — Short title
```

For completed work, keep **`[DONE]`** as the priority slot:

```markdown
## [DONE] <scope> T<n> — Short title
```

**User and agent references:** refer to a task by **`T<n>`** (e.g. `task T12`, `unblock T7`).

### Task `Status` values (placement-aware)

| `Status` | Typical section | Notes |
|----------|-----------------|--------|
| `NOT_STARTED` | Active or Backlog | Queued; may sit in either section per repo convention |
| `IN_PROGRESS` | **Active Tasks** only | Primary WIP row |
| `BLOCKED` | Active (or Backlog if not yet started) | Use **`Blockers:`** field |
| `INTERRUPTED` | **Active Tasks** only | Session ended mid-task |
| `POSTPONED` | **Backlog only** | **Hard rule:** any row with `Status: POSTPONED` **must** appear **under `# Backlog`** (after that heading). **Never** under `# Active Tasks`. Resume by moving to Active (or keep in Backlog) and set `NOT_STARTED` / `IN_PROGRESS` as appropriate |

Other terminal states: `DONE` (Completed section), `CANCELLED` (Cancelled section or noted inline).

### Allowed `scope` values (closed list)

Expand this list only by an explicit project decision (e.g. row in `.agent/decisions.md`).

| `scope` | Use for |
|---------|---------|
| `feat` | New capability or materially new behavior |
| `fix` | Bug fix, regression, incorrect behavior |
| `chore` | Small cleanup, polish, trivial maintenance without contract change |
| `audit` | Consistency review, alignment, repo/process audit follow-ups |
| `docs` | Primarily documentation / agent-facing prose |
| `refactor` | Same external behavior, structure or code reorganized |
| `infra` | CI, scripts, environment, template sync mechanics |
| `research` | Exploration without committing to a deliverable in the same pass |
| `meta` | Task system, templates, hub rules about how agents work |
| `test` | Failing tests, test coverage gaps, test infrastructure fixes |

### Allocating the next `T<n>`

1. Read **all** of `.agent/tasks.md` (every section: Backlog, Active, Completed, Cancelled, **Archive** if present).
2. Collect every **`T` + digits** that appears in an **H2 task heading** matching `## [` … `] <scope> T<n> —` **or in Archive table rows** matching `| T\d+ |` (pattern `\bT\d+\b` in those lines is sufficient).
3. Let **`max`** be the maximum numeric part. **Next id is `T{max + 1}`** (or **`T1`** if none exist).
4. **Never** reuse a number. **Do not** renumber existing tasks except during a documented, one-off migration.

## File Structure

```
repo-root/
└── .agent/
    └── tasks.md           # Active and completed task tracking
```

## Read on Session Start

1. **Read .agent/tasks.md** — check for:
   - `[IN_PROGRESS]` tasks — continue work
   - `[BLOCKED]` tasks — check if blockers resolved
   - `[INTERRUPTED]` tasks — restore context first
   - **`# Backlog`** rows with `Status: POSTPONED` — intentionally deprioritized; do not treat as active WIP
   - `[HIGH]` / `[CRITICAL]` tasks — prioritize these
   - Task **`T<n>`** if the user refers to a number
   - **`# Archive`** section — check archived IDs (still count for max T)

2. Acknowledge: "Tasks loaded: [X active, Y blocked, Z interrupted, W postponed in backlog, V archived], max T…"

## Task Lifecycle

### 1. Creating a New Task

When user requests work or you identify a new task:

1. Allocate **`T<n>`** per **Allocating the next `T<n>`** above.
2. Choose **`scope`** from the allowed list.
3. Write:

```markdown
## [PRIORITY] <scope> T<n> — Short title
Status: NOT_STARTED
Created: YYYY-MM-DDTHH:mm:ssZ
Last worked: YYYY-MM-DDTHH:mm:ssZ
Next step: (concrete first action)
Notes: (optional context)
```
(UTC only; format per `~/.config/kimi/prompts/settings.md` § Timestamps.)

Priority levels (active / not done): `CRITICAL` > `HIGH` > `MEDIUM` > `LOW`

### 2. Starting Work

Change status and update timestamp:

```markdown
Status: IN_PROGRESS
Last worked: YYYY-MM-DDTHH:mm:ssZ
```
(use current UTC instant per `~/.config/kimi/prompts/settings.md` § Timestamps)

### 3. Blocking / Unblocking

If blocked:
```markdown
Status: BLOCKED
Blockers: (specific what's needed to unblock; cite other tasks as T<id> if useful)
```

When unblocked:
```markdown
Status: IN_PROGRESS
Blockers: (cleared: what changed)
```

### 4. Task Interruption

If session ends mid-task:
```markdown
Status: INTERRUPTED
Last worked: YYYY-MM-DDTHH:mm:ssZ
Notes: (current state, what's next, any temp files/branches)
```
(per `~/.config/kimi/prompts/settings.md` § Timestamps)

### 5. Postponing (Backlog-only)

When work is deliberately deferred (not blocked—just out of scope for now):

1. Move the task **heading + body** so the row lives **under `# Backlog`** (never under `# Active Tasks`).
2. Set:

```markdown
Status: POSTPONED
Last worked: YYYY-MM-DDTHH:mm:ssZ
Postponed: (why / until when / trigger to revisit)
Next step: (first action when un-postponed)
```

3. **Do not** use `POSTPONED` for tasks that remain under **Active**—that placement is invalid; use `BLOCKED` or move to Backlog first.

**Resume from POSTPONED:** move row to `# Active Tasks` if it becomes WIP, then set `Status: NOT_STARTED` or `IN_PROGRESS` and clear or shorten **Postponed:** once no longer deferred.

### 6. Completing a Task

Move to `# Completed Tasks` section. **Keep `T<n>` and `scope` in the heading.**

```markdown
## [DONE] <scope> T<n> — Short title
Completed: YYYY-MM-DDTHH:mm:ssZ
Summary: (what was accomplished, key outcomes)
```

### 7. Cancelling / splitting

- **Cancelled:** move to a `# Cancelled Tasks` section (or keep with `Status: CANCELLED`) — **same `T<n>`**, note reason; **do not** reuse `n`.
- **Split:** new work gets a **new** `T`; in the original task's **Notes**: `split → T<new>`.

### 8. Archiving completed/cancelled tasks (user-commanded only)

When user explicitly requests to archive/cleanup/compress/compact completed and cancelled tasks (trigger phrases: "archive tasks", "clean up completed", "clear task log", "compress finished tasks", "archive done", "compact tasks", "archive completed"):

1. **Collect** all tasks from `# Completed Tasks` and `# Cancelled Tasks` sections
2. **Sort** tasks: first by **Date** (ascending), then by **ID** (ascending, numeric) — oldest first, stable within same date
3. **Convert** to **compressed table format** (ID, Date, Scope, Status, Title) in sorted order
4. **Append** to `# Archive` section at end of file (create if not exists)
5. **Preserve** all `T<n>` identifiers — archived IDs **still count** for next allocation
6. **Clear** Completed/Cancelled sections (leave headers, remove full task bodies)

**Archive table format:**

```markdown
# Archive

<!-- Compressed history — T<n> preserved for ID continuity. Never remove rows. -->

| ID | Date | Scope | Status | Title |
|----|------|-------|--------|-------|
| T1 | 2026-03-20 | feat | DONE | Initialize project documentation |
| T3 | 2026-03-24 | fix | CANCELLED | Login timeout bug |
| T5 | 2026-03-24 | infra | DONE | Set up CI/CD pipeline |
| T7 | 2026-03-25 | test | DONE | Fix flaky auth test |
```

**Critical rules:**
- Archive is **append-only** — never edit or delete archived rows
- When allocating next `T<n>`, scan **Archive section too** — include all `| T\d+ |` matches
- Archive grows indefinitely; old rows remain forever
- **User command required** — do not auto-archive without explicit request
- After archiving, report: "Archived N completed/cancelled tasks to # Archive. Max T<n> unchanged (still T<max>)."

## Save Work / Persist state (this protocol only)

When a **checkpoint** runs (triggers and order: **`~/.config/kimi/templates/agent.md`** or **`.agent/intro.md`** § SKILLS → *Persist state*), this protocol's **sole** responsibility is **`.agent/tasks.md`**.

1. Set each **active** task's `Status` to match reality (`DONE`, `IN_PROGRESS`, `INTERRUPTED`, `BLOCKED`, `NOT_STARTED`, `POSTPONED`, etc.). If any row has `Status: POSTPONED`, **confirm** it sits **under `# Backlog`**; relocate the row if not.
2. Update **`Last worked`** to the current UTC UTC instant in **`YYYY-MM-DDTHH:mm:ssZ`** (per `~/.config/kimi/prompts/settings.md` § Timestamps) for every task you touched during this checkpoint.
3. If work stops mid-task: use `INTERRUPTED` and expand **Notes** with the next concrete step and WIP context (branch, failing paths, temp artifacts).
4. **Do not** change **`T<n>`** or `scope` in headings unless correcting a documented error.

This step runs **after** **memory-protocol** and **decision-protocol** in the template order; then **knowledge-protocol**, then **style-protocol**, then **glossary-protocol** when its **Write gate** applies — do not skip knowledge unless the skip rule applies.

## Task Hygiene Rules

- **Respect .gitignore** — Never create tasks that involve modifying files in `.gitignore`
  (except `.agent/` directory). Always check .gitignore first.
- **One task at a time** — avoid multiple IN_PROGRESS tasks
- **POSTPONED lives in Backlog** — never an Active Tasks row; violates protocol → move under `# Backlog` on sight
- **Specific next steps** — vague "continue work" is not helpful
- **Clear blockers** — state exactly what's needed to unblock; reference **`T<id>`** for sibling tasks
- **Archive completed** — move to Completed Tasks, don't delete
- **Archive on user command only** — never auto-archive; wait for explicit trigger phrase
- **Stable IDs** — `T<n>` is immutable for the life of that task row; titles may be edited

## Cross-Session Continuity

- On resume: read `[INTERRUPTED]` tasks first
- Restore context from Notes before accepting new work
- Update status from INTERRUPTED → IN_PROGRESS when resuming

## Example Task Entries

### Active Task
```markdown
## [HIGH] feat T24 — Implement user authentication
Status: IN_PROGRESS
Created: 2026-03-25T09:00:00Z
Last worked: 2026-03-27T14:00:00Z
Next step: Add JWT token validation middleware
Notes: OAuth flow working; blocked by T23 (API keys). Branch `feat/auth`.
```

### Blocked Task
```markdown
## [MEDIUM] refactor T31 — Optimize database queries
Status: BLOCKED
Created: 2026-03-26T10:00:00Z
Last worked: 2026-03-26T16:00:00Z
Blockers: Waiting for DBA to provide query execution plan
Next step: Review execution plan and identify indexes
```

### Interrupted Task
```markdown
## [HIGH] fix T28 — Refactor API error handling
Status: INTERRUPTED
Created: 2026-03-20T11:00:00Z
Last worked: 2026-03-27T18:00:00Z
Next step: Update test suite for changed signatures
Notes: 12/15 endpoints fixed. Tests failing in `tests/test_api_v2.py`. Branch `fix/api-errors`.
```

### Completed Task
```markdown
## [DONE] infra T22 — Set up CI/CD pipeline
Completed: 2026-03-24T12:00:00Z
Summary: Configured GitHub Actions with test, lint, and deploy jobs. Pipeline runs on PR and merge to main.
```

### Postponed (Backlog)
```markdown
## [LOW] research T33 — Spike on alternative SDK
Status: POSTPONED
Created: 2026-03-20T09:00:00Z
Last worked: 2026-03-27T10:00:00Z
Postponed: Await product decision on vendor; revisit next quarter
Next step: Re-read vendor docs and prototype auth flow
Notes: (optional)
```
**(Placement)** this block must appear only under **`# Backlog`**, not under **`# Active Tasks`**.
<!-- END OF PROTOCOL COPY -->

## [DONE] meta T1 — Initialize project documentation
Status: DONE
Created: 2026-04-06T16:28:17Z
Last worked: 2026-04-06T16:28:17Z
Next step: Review .agent/intro.md for accuracy
Notes: Initial setup by repo-init-agent; migrated from agent.old structure

## [CRITICAL] fix T2 — Fix unreachable code in SDK logging setup
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/logging.py:24`
Next step: Remove premature return or move it to end of function
Notes: `return level, filepath` on line 24 makes all subsequent logging configuration unreachable. File logs never created.

## [CRITICAL] fix T3 — Enable SSL verification by default in HTTP client
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/http/client.py:219`
Next step: Change `verify: str | bool = False` to `verify: str | bool = True`
Notes: MITM vulnerability. SSL verification disabled by default.

## [CRITICAL] fix T4 — Remove passwords from URL parameters in API client
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api-client/api_client/v1.py:102-116`
Next step: Use POST request with body instead of GET with params for check_live_stream_auth
Notes: Credentials exposed in server logs, browser history, proxy logs. Method `check_live_stream_auth` sends username/password in URL params.

## [CRITICAL] fix T5 — Replace MD5 password hashing with bcrypt/Argon2
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/core/models/user.py:125,132`
Next step: Use Django's make_password/check_password with bcrypt or Argon2
Notes: MD5 critically vulnerable to brute force and rainbow tables. Lines 125 and 132 use md5().hexdigest().

## [CRITICAL] fix T6 — Fix ALLOWED_HOSTS wildcard
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/settings/prod.py:18`
Next step: Replace `["*"]` with specific domain(s)
Notes: HTTP Host Header attacks, DNS Rebinding possible.

## [CRITICAL] fix T7 — Add path validation in FileViewSet download
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/storage/views/file.py:49`
Next step: Validate instance.filepath against path traversal before using in os.path.join
Notes: Path traversal vulnerability. `../../../etc/passwd` possible.

## [CRITICAL] fix T8 — Add path validation in FileViewSet perform_destroy
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/storage/views/file.py:68-70`
Next step: Validate instance.filepath before os.path.join with settings.CONFIG.storage.path
Notes: Path traversal allows deletion of arbitrary files.

## [CRITICAL] fix T9 — Close file descriptor in podcast upload
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/worker/worker/tasks.py:151`
Next step: Use context manager `with open(...) as f:` instead of inline open()
Notes: File descriptor leak. `open(tmp_file.name, "rb")` never closed.

## [CRITICAL] fix T10 — Fix mutable class state in StatusReporter
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/status_reporter.py:218`
Next step: Move `_ipc_queue` to __init__ as instance variable
Notes: `queue.Queue()` at class level shared across all processes/threads. Race conditions possible.

## [CRITICAL] fix T11 — Add timeout to socket receive loop
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/liquidsoap/client/_connection.py:87-88`
Next step: Add timeout and break condition to while loop
Notes: Infinite loop if Liquidsoap keeps sending data. `while self._sock.recv(2**10)` never exits.

## [CRITICAL] fix T12 — Fix race condition in queue popleft
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/player/queue.py:60`
Next step: Use atomic operation or proper locking between len() check and popleft()
Notes: IndexError if another thread clears deque between check and pop.

## [CRITICAL] fix T13 — Replace pickle with JSON in status reporter
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/status_reporter.py:66-67`
Next step: Use json.load instead of pickle.load
Notes: RCE vulnerability. pickle.load on user-controlled file path.

## [CRITICAL] fix T14 — Fix unbounded timer leak in fetch.py
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/player/fetch.py:347`
Next step: Store timer reference and cancel on shutdown
Notes: Infinite timer chain creates zombie threads on shutdown.

## [CRITICAL] fix T15 — Add timeout to HTTP request in status reporter
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/status_reporter.py:202-208`
Next step: Add timeout parameter to requests.get()
Notes: Request can hang forever blocking retry loop.

## [CRITICAL] fix T16 — Fix retry decorator silent failure
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api-client/api_client/v1.py:28-49`
Next step: Raise exception instead of returning None when retries exhausted
Notes: Silent failure hides errors. Function returns None on failure.

## [CRITICAL] fix T17 — Remove sys.exit from config validation
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/config/_base.py:56-58`
Next step: Raise exception instead of sys.exit(1)
Notes: Library must not terminate process. Error handling impossible.

## [HIGH] fix T18 — Add transaction atomic to FileViewSet destroy
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/storage/views/file.py:54-85`
Next step: Add @transaction.atomic and select_for_update()
Notes: TOCTOU race between check and delete.

## [HIGH] fix T19 — Replace fields __all__ with explicit list in serializers
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
Files: Multiple (file.py:14, podcast.py:18,25,32,39, show.py:48,56,64,72, playlist.py:14,22)
Next step: Specify explicit fields list in each serializer Meta class
Notes: Mass assignment vulnerability. Fields exposed unintentionally.

## [HIGH] fix T20 — Add rate limiting to authentication endpoints
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/`
Next step: Implement Django Ratelimit or similar on login/API-key endpoints
Notes: No brute force protection.

## [HIGH] fix T21 — Fix memory leak in get_own_obj permissions
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/permissions.py:36-46`
Next step: Add pagination or limit queryset, use exists() instead of iteration
Notes: Full table loaded into memory. DoS with millions of records.

## [HIGH] fix T22 — Hash live_auth_custom_password
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/schedule/models/show.py:66-77`
Next step: Add password hashing on save, verify on check
Notes: Password stored in plain text.

## [HIGH] fix T23 — Fix mutable class variable in HTTP client
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/http/client.py:252-255`
Next step: Move Headers to __init__ as instance variable
Notes: Class-level dict modified by all instances.

## [HIGH] fix T24 — Add cache size limit to HTTP client
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/http/client.py:250`
Next step: Use LRU cache or limit _instances dict size
Notes: Unbounded cache causes memory leak.

## [HIGH] fix T25 — Close requests session properly
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api-client/api_client/_client.py:54-99`
Next step: Implement close() method or context manager
Notes: Connection leak. Session never closed.

## [HIGH] fix T26 — Add empty response check in liquidsoap client
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/liquidsoap/client/_client.py:91`
Next step: Check if splitlines() returns empty list before indexing
Notes: IndexError on empty response from server.

## [HIGH] fix T27 — Fix infinite loop in wait_for_version
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/liquidsoap/client/_client.py:60-74`
Next step: Decrement timeout on any exception, not just OSError
Notes: Infinite loop if non-OSError exception raised.

## [HIGH] fix T28 — Add graceful shutdown mechanism to threads
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
Files: player/fetch.py:371, player/push.py:52,106, player/file.py:170, player/queue.py:42, history/stats.py:165
Next step: Add Event/Flag for thread shutdown instead of `while True`
Notes: Threads don't stop on SIGTERM.

## [HIGH] fix T29 — Validate URL in podcast download task
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/worker/worker/tasks.py:97`
Next step: Add URL validation, block file:// and internal schemes
Notes: SSRF vulnerability. file:///etc/passwd possible.

## [HIGH] fix T30 — Fix TOCTOU in organise_file
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/pipeline/organise_file.py:42-54`
Next step: Use try/except instead of check-then-act pattern
Notes: Race between is_file() and samefile().

## [HIGH] fix T31 — Handle errors in analyze_cuepoint
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/pipeline/analyze_cuepoint.py:41-43`
Next step: Don't silently pass on CalledProcessError, log or raise
Notes: ffmpeg errors ignored, metadata in undefined state.

## [HIGH] fix T32 — Fix PIPE deadlock in subprocess
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/pipeline/_utils.py:8-16`
Next step: Use temporary files for stdout/stderr instead of PIPE
Notes: Deadlock when ffmpeg output fills buffer.

## [HIGH] fix T33 — Add file existence check in analyze_metadata
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/pipeline/analyze_metadata.py:42-43`
Next step: Check filepath.exists() before stat() and compute_md5()
Notes: FileNotFoundError if file deleted between message and processing.

## [HIGH] fix T34 — Fix API key validation IndexError
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/permissions.py:66-73`
Next step: Check split() result length before indexing [1]
Notes: IndexError if header is just "Api-Key" without token.

## [HIGH] fix T35 — Fix user comparison in permissions
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/permissions.py:96`
Next step: Compare obj.username with request.user.username, not request.user
Notes: str vs User object comparison always False.

## [MEDIUM] fix T36 — Mask Authorization header in error logs
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/middlewares.py:10-17`
Notes: All headers logged on error including Authorization.

## [MEDIUM] fix T37 — Add URL validation to Podcast model
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/podcasts/models/podcast.py:4-11`
Notes: No URL validation, file:// and other schemes allowed.

## [MEDIUM] fix T38 — Fix uninitialized variable in queue.py
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/player/queue.py:43-56`
Notes: media_schedule may be undefined on Empty exception.

## [MEDIUM] fix T39 — Add API response validation in schedule
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/player/schedule.py:124-146`
Notes: KeyError if required fields missing from API response.

## [MEDIUM] fix T40 — Fix signal handler redefinition
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/message_handler.py:114-117`
Notes: Handler recreated on every RabbitMQ reconnect.

## [MEDIUM] fix T41 — Add rollback on pipeline error
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/analyzer/analyzer/pipeline/pipeline.py:70-111`
Notes: File remains in storage on FAILED status.

## [MEDIUM] fix T42 — Add thread safety to queue tracker
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/player/liquidsoap.py:189-194`
Notes: liq_queue_tracker accessed from multiple threads without Lock.

## [MEDIUM] fix T43 — Add locking to instance cache
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/http/client.py:264-298`
Notes: Race condition on _instances dict.

## [MEDIUM] fix T44 — Fix logger iteration race condition
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/structlog.py:243`
Notes: loggerDict modified during iteration.

## [MEDIUM] fix T45 — Fix Exception args order
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/http/exceptions.py:466-487`
Notes: Non-standard Exception args order breaks error handling.

## [MEDIUM] fix T46 — Fix falsy value handling in config merge
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/config/_base.py:88-108`
Notes: `if value` skips valid falsy values (0, False, "").

## [MEDIUM] fix T47 — Add Celery max_instances
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/worker/worker/tasks.py:48-53`
Notes: No rate limiting, memory leak on task accumulation.

## [MEDIUM] fix T48 — Add select_related to get_owner methods
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
Files: Multiple models with get_owner()
Notes: N+1 query problem.

## [MEDIUM] fix T49 — Add CSRF protection for session auth
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/settings/_internal.py:154-156`
Notes: SessionAuthentication without CSRF enforcement.

## [MEDIUM] fix T50 — Close history stats session properly
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/history/stats.py:39`
Notes: TCP connection leak on shutdown.

## [LOW] chore T51 — Fix typo in webstream permission name
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/schedule/views/webstream.py:26`
Notes: "webstreametadata" should be "webstreammetadata".

## [LOW] chore T52 — Remove unused import in file view
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/storage/views/file.py:3`
Notes: `from os import remove` unused (uses os.remove).

## [LOW] chore T53 — Update deprecated Celery backend
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/worker/worker/config.py:18`
Notes: "amqp" deprecated in Celery 5.x.

## [LOW] chore T54 — Replace MD5 with SHA256 for file hashes
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/files.py:11`
Notes: Not critical for file hashes but better to use SHA256.

## [LOW] chore T55 — Remove duplicate in __all__
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/__init__.py:13-22`
Notes: "config" appears twice.

## [LOW] chore T56 — Fix inconsistent media_id typing
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
Files: `app/api-client/api_client/v1.py:118-128`, `app/api-client/api_client/v2.py:249-262`
Notes: str vs int inconsistency.

## [LOW] chore T57 — Fix variable scoping in fetch.py exception handler
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/playout/playout/player/fetch.py:371-409`
Notes: `log` variable may be undefined if exception before assignment.

## [MEDIUM] test T58 — Fix failing SDK compat test (UTC.dst returns None)
Status: NOT_STARTED
Created: 2026-04-06T21:20:00Z
Last worked: 2026-04-06T21:20:00Z
File: `tests/unit/sdk/test_compat.py:21`
Next step: Fix test expectation - UTC.dst(None) returns None, not timedelta(0)
Notes: Test expects UTC.dst(None) == timedelta(0), but Python's timezone.utc.dst(None) returns None.

## [MEDIUM] test T59 — Fix failing datetime test (max time milliseconds)
Status: NOT_STARTED
Created: 2026-04-06T21:20:00Z
Last worked: 2026-04-06T21:20:00Z
File: `tests/unit/sdk/test_datetime.py:58-62`
Next step: Fix expected value calculation for max time
Notes: Test calculation for max time milliseconds is incorrect. time(23, 59, 59, 999999) has 999999 microseconds, not 0.999999 seconds.

## [MEDIUM] test T60 — Fix failing config merge tests (type coercion)
Status: NOT_STARTED
Created: 2026-04-06T21:20:00Z
Last worked: 2026-04-06T21:20:00Z
Files: `tests/unit/sdk/config/test_base.py` (multiple tests)
Next step: Fix test expectations for type handling in merge functions
Notes: Multiple tests fail because they expect incorrect type coercion behavior (int to str, None handling in lists).

## [MEDIUM] test T61 — Fix import error in SDK config models test
Status: NOT_STARTED
Created: 2026-04-06T21:20:00Z
Last worked: 2026-04-06T21:20:00Z
File: `tests/unit/sdk/config/test_models.py:7`
Next step: Fix import - BaseHarborInput does not exist, use HarborInput
Notes: Test tries to import BaseHarborInput which doesn't exist. Should be HarborInput.

## [MEDIUM] test T62 — Fix failing env loader tests
Status: NOT_STARTED
Created: 2026-04-06T21:20:00Z
Last worked: 2026-04-06T21:20:00Z
File: `tests/unit/sdk/config/test_env.py`
Next step: Fix test expectations for env array index parsing and schema composition
Notes: Multiple tests fail due to incorrect expectations about env var parsing behavior.

## [MEDIUM] test T63 — Fix failing fields validation tests
Status: NOT_STARTED
Created: 2026-04-06T21:20:00Z
Last worked: 2026-04-06T21:20:00Z
File: `tests/unit/sdk/config/test_fields.py`
Next step: Fix test expectations for StrNoTrailingSlash and AnyUrlStr validation
Notes: Tests expect validation errors that don't occur (int coerced to str) or don't raise on invalid URL scheme.

# Backlog

<!--
New work queue (optional):
## [PRIORITY] <scope> T<n> — Short title
Status: NOT_STARTED | POSTPONED
Created: YYYY-MM-DDTHH:mm:ssZ (UTC)
Last worked: YYYY-MM-DDTHH:mm:ssZ (UTC)
Postponed: (if POSTPONED — why / until; POSTPONED rows must stay under # Backlog only, never under # Active Tasks)
Blockers: (if BLOCKED)
Next step: (concrete action)
Notes: (optional context; reference other tasks as T<id>)
-->

# Completed Tasks

<!-- 
When done, move under # Completed Tasks:
## [DONE] <scope> T<n> — Short title
Completed: YYYY-MM-DDTHH:mm:ssZ (UTC)
Summary: (what was accomplished)

User command "archive tasks"/"compact tasks" moves these to # Archive in table format.
-->

## [DONE] meta T1 — Initialize project documentation
Status: DONE
Created: 2026-04-06T16:28:17Z
Last worked: 2026-04-06T16:28:17Z
Next step: Review .agent/intro.md for accuracy
Notes: Initial setup by repo-init-agent; migrated from agent.old structure

# Cancelled Tasks

<!--
Cancelled work (optional):
## [CANCELLED] <scope> T<n> — Short title
Status: CANCELLED
Created: YYYY-MM-DDTHH:mm:ssZ (UTC)
Cancelled: YYYY-MM-DDTHH:mm:ssZ (UTC)
Reason: (why cancelled)

User command "archive tasks"/"compact tasks" moves these to # Archive in table format.
-->

# Archive

<!--
Compressed history — user-commanded archive of completed/cancelled tasks.
Append-only: never edit or delete rows. T<n> preserved for ID continuity.
Scan this section when allocating next T<n> (max+1 rule).

| ID | Date | Scope | Status | Title |
|----|------|-------|--------|-------|
-->
