# Active Tasks

<!-- Protocol: ~/.config/kimi/skills/task-protocol/SKILL.md (modified: 2026-04-07T12:03:05Z, commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7) -->
<!-- The following section is a FULL COPY of ~/.config/kimi/skills/task-protocol/SKILL.md
     Protocol commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7
     Protocol modified: 2026-04-07T12:03:05Z -->
---
name: task-protocol
description: Protocol for maintaining .agent/tasks.md task tracking and work item management
---

# Task Protocol

Task tracking system for managing active, blocked, and completed work items across AI agent sessions.

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
Notes: (optional)
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
2. Update **`Last worked`** to the current UTC instant in **`YYYY-MM-DDTHH:mm:ssZ`** (per `~/.config/kimi/prompts/settings.md` § Timestamps) for every task you touched during this checkpoint.
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

---

# LEGACY TESTING PLAN — Phase 0: Foundation (Weeks 1-2)

## [DONE] test T64 — Fix PreferenceUnitTest.php path issue
Status: DONE
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:46:18Z
Completed: 2026-04-07T13:46:18Z
Summary: Fixed relative path issues in 3 test files by replacing `../application/configs/conf.php` with `CONFIG_PATH . '/conf.php'`. Files: PreferenceUnitTest.php, ShowServiceUnitTest.php, ShowServiceDbTest.php. Tests now load successfully in Docker environment.

## [DONE] test T65 — Audit all require_once in tests/ for relative paths
Status: DONE
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:51:18Z
Completed: 2026-04-07T13:51:18Z
Summary: Completed audit of all require_once in tests/. Found and fixed 3 files with relative paths (T64). All remaining require_once use proper constants (CONFIG_PATH, APPLICATION_PATH) or __DIR__ which resolves correctly in Docker. No additional path fixes needed.

## [MEDIUM] test T66 — Create unified TestBootstrap.php
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/TestBootstrap.php`
Next step: Create single entry point that sets constants and loads dependencies
Notes: Blocked by T65. Must know all path patterns before consolidating.

## [MEDIUM] test T67 — Verify phpunit.xml bootstrap configuration
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/phpunit.xml`
Next step: Ensure bootstrap file loads correctly with all required constants
Notes: Blocked by T66. Update after TestBootstrap.php created.

## [MEDIUM] test T68 — Test TestHelper::getDbZendConfig()
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/TestHelper.php`
Next step: Create unit test for getDbZendConfig() method
Notes: Part of Test Helpers Coverage goal

## [MEDIUM] test T69 — Test TestHelper::installTestDatabase()
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/TestHelper.php`
Next step: Create unit test for installTestDatabase() method
Notes: Depends on working database fixtures

## [MEDIUM] test T70 — Test AirtimeInstall::CreateDatabaseTables()
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/AirtimeInstall.php`
Next step: Test SQL migrations execution
Notes: Already patched for Docker paths; needs test coverage

## [MEDIUM] test T71 — Create ModelFactory for test fixtures
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/ModelFactory.php`
Next step: Design fluent API for creating test models
Notes: Blocked by T72-T74. Must understand entity relationships first.

## [MEDIUM] test T72 — Create YAML fixtures for User entity
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/fixtures/users.yml`
Next step: Create YAML fixture with test user data
Notes: Base fixture for auth tests

## [MEDIUM] test T73 — Create YAML fixtures for Show entity
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/fixtures/shows.yml`
Next step: Create YAML fixture with test show data
Notes: Critical for ShowService tests

## [MEDIUM] test T74 — Create YAML fixtures for File entity
Status: NOT_STARTED
Phase: 0
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/fixtures/files.yml`
Next step: Create YAML fixture with test file data
Notes: Required for MediaService tests

---

# LEGACY TESTING PLAN — Phase 1: Common Helpers (Weeks 2-3)

## [MEDIUM] test T75 — Test DateHelper::getUTCDateTime()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/DateHelperTest.php`
Next step: Test valid/invalid date parsing
Notes: Pure function, high value, easy to test

## [MEDIUM] test T76 — Test DateHelper::getLocalDateTime()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/DateHelperTest.php`
Next step: Test timezone conversion logic
Notes: Depends on timezone configuration

## [MEDIUM] test T77 — Test DateHelper::getTimeInterval()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/DateHelperTest.php`
Next step: Test interval calculations
Notes: Edge cases around DST transitions

## [MEDIUM] test T78 — Test DateHelper::isInPast()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/DateHelperTest.php`
Next step: Test boundary conditions
Notes: Critical for scheduling logic

## [MEDIUM] test T79 — Test DateHelper::getDateRange()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/DateHelperTest.php`
Next step: Test date range generation
Notes: Used in calendar views

## [MEDIUM] test T80 — Test FileDataHelper::createFileFromUpload()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/FileDataHelperTest.php`
Next step: Test valid file upload handling
Notes: May need mock filesystem

## [MEDIUM] test T81 — Test FileDataHelper::parseMetadata()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/FileDataHelperTest.php`
Next step: Test ID3/exif metadata extraction
Notes: Requires test audio files

## [MEDIUM] test T82 — Test FileDataHelper::validateFileExtension()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/FileDataHelperTest.php`
Next step: Test allowed/blocked extensions
Notes: Security-critical function

## [MEDIUM] test T83 — Test FileDataHelper::sanitizeFilename()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/FileDataHelperTest.php`
Next step: Test filename sanitization
Notes: Prevents path traversal

## [MEDIUM] test T84 — Test FileDataHelper::getMimeType()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/FileDataHelperTest.php`
Next step: Test MIME type detection
Notes: Used for file validation

## [LOW] test T85 — Test HTTPHelper::getClientIp()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/HTTPHelperTest.php`
Next step: Test IP extraction from headers
Notes: X-Forwarded-For handling

## [LOW] test T86 — Test HTTPHelper::isAjaxRequest()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/HTTPHelperTest.php`
Next step: Test XHR detection
Notes: Simple header check

## [LOW] test T87 — Test HTTPHelper::buildUrl()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/HTTPHelperTest.php`
Next step: Test URL construction
Notes: Query string handling

## [MEDIUM] test T88 — Test SecurityHelper::generateToken()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/SecurityHelperTest.php`
Next step: Test token generation
Notes: CSRF/auth token generation

## [MEDIUM] test T89 — Test SecurityHelper::hashPassword()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/SecurityHelperTest.php`
Next step: Test password hashing
Notes: Uses MD5 currently (known issue)

## [MEDIUM] test T90 — Test SecurityHelper::verifyCsrfToken()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/SecurityHelperTest.php`
Next step: Test CSRF protection
Notes: Security-critical

## [MEDIUM] test T91 — Test SecurityHelper::sanitizeInput()
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/SecurityHelperTest.php`
Next step: Test XSS prevention
Notes: Input sanitization

## [LOW] test T92 — Test LocaleHelper methods
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/LocaleHelperTest.php`
Next step: Test getAvailableLocales, normalizeLanguageCode, getDateFormat
Notes: Low priority, simple functions

## [LOW] test T93 — Test OsPath methods
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/OsPathTest.php`
Next step: Test join, normalize, isAbsolute
Notes: Path utilities

## [LOW] test T94 — Test Timezone methods
Status: NOT_STARTED
Phase: 1
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/helpers/TimezoneTest.php`
Next step: Test getUserTimezone, convertToUTC, getTimezoneList
Notes: Timezone handling

---

# LEGACY TESTING PLAN — Phase 2: Service Layer — Core (Weeks 3-5)

## [CRITICAL] test T95 — Test ShowService::addUpdateShow() without repeat
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test creating single show instance
Notes: Critical path — show creation is core functionality

## [CRITICAL] test T96 — Test ShowService::addUpdateShow() with weekly repeat
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test weekly recurring shows
Notes: Most common repeat type

## [CRITICAL] test T97 — Test ShowService::addUpdateShow() with bi-weekly repeat
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test bi-weekly recurring shows
Notes: Edge case in repeat logic

## [CRITICAL] test T98 — Test ShowService::addUpdateShow() with monthly repeat
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test monthly recurring shows
Notes: Complex date math

## [HIGH] test T99 — Test ShowService::addUpdateShow() with rebroadcast
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test rebroadcast functionality
Notes: Advanced feature

## [HIGH] test T100 — Test ShowService::addUpdateShow() with recording
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test recording-enabled shows
Notes: Requires storage mocks

## [HIGH] test T101 — Test ShowService editing without changing repeat
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test editing show metadata only
Notes: Update operations

## [HIGH] test T102 — Test ShowService changing repeat type
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test weekly → bi-weekly transition
Notes: Complex state change

## [HIGH] test T103 — Test ShowService deleting instances
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test single, current+following, full show deletion
Notes: Delete operations critical

## [HIGH] test T104 — Test ShowService query methods
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test getFutureShowInstances, getShowLength, formatShowDuration
Notes: Read operations

## [MEDIUM] test T105 — Test ShowService private methods via Reflection
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/ShowServiceTest.php`
Next step: Test createUTCStartEndDateTime, getNextMonthlyWeeklyRepeatDate, etc.
Notes: Complex date logic needs coverage

## [HIGH] test T106 — Test SchedulerService methods
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/SchedulerServiceTest.php`
Next step: Test scheduleAfter, removeGaps, reschedule, isScheduleEmpty
Notes: Core scheduling logic

## [HIGH] test T107 — Test UserService CRUD operations
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/UserServiceTest.php`
Next step: Test createUser, updateUser, deleteUser, getUserByLogin
Notes: User management

## [HIGH] test T108 — Test UserService authentication methods
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/UserServiceTest.php`
Next step: Test changePassword, validateUserType
Notes: Auth-related operations

## [HIGH] test T109 — Test MediaService file operations
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/MediaServiceTest.php`
Next step: Test uploadFile, updateMetadata, deleteFile, moveFile, searchFiles
Notes: File management critical

## [MEDIUM] test T110 — Test PodcastService methods
Status: NOT_STARTED
Phase: 2
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/services/PodcastServiceTest.php`
Next step: Test importPodcast, updatePodcast, deletePodcast, syncEpisodes
Notes: RSS podcast integration

---

# LEGACY TESTING PLAN — Phase 3: Models — Core (Weeks 5-7)

## [CRITICAL] test T111 — Test Show Model basic CRUD
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/ShowModelTest.php`
Next step: Test getName/setName, getDescription/setDescription, getColor/setColor
Notes: Core entity

## [CRITICAL] test T112 — Test Show Model host management
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/ShowModelTest.php`
Next step: Test getHosts, addHost, removeHost
Notes: Host assignment critical

## [CRITICAL] test T113 — Test Show Model recording flag
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/ShowModelTest.php`
Next step: Test isRecorded method
Notes: Recording functionality

## [CRITICAL] test T114 — Test ShowInstance Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/ShowInstanceModelTest.php`
Next step: Test getShow, getStartDateTime, getEndDateTime, addFileToShow, clearShow
Notes: Show instances are core to scheduling

## [CRITICAL] test T115 — Test Schedule Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/ScheduleModelTest.php`
Next step: Test IsFileScheduledInTheFuture, checkOverlappingShows, getRangeScheduled
Notes: Scheduling engine

## [HIGH] test T116 — Test Block Model (Smart Blocks)
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/BlockModelTest.php`
Next step: Test saveSmartBlockCriteria, getListOfFilesUnderLimit, getLength
Notes: Smart block functionality

## [HIGH] test T117 — Test Playlist Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/PlaylistModelTest.php`
Next step: Test create, addContent, moveItem, deleteItem, getLength
Notes: Playlist management

## [HIGH] test T118 — Test StoredFile Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/StoredFileModelTest.php`
Next step: Test create, updateMetadata, delete, getMetadata
Notes: File metadata handling

## [HIGH] test T119 — Test User Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/UserModelTest.php`
Next step: Test create, setPassword, checkPassword, getType, isAdmin
Notes: User authentication

## [MEDIUM] test T120 — Test Preference Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/PreferenceModelTest.php`
Next step: Test SetValue/GetValue, SetShowsPopulatedUntil, GetShowsPopulatedUntil
Notes: System preferences

## [MEDIUM] test T121 — Test Library Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/LibraryModelTest.php`
Next step: Test getFiles, search, getFileCount
Notes: Library browsing

## [MEDIUM] test T122 — Test Webstream Model
Status: NOT_STARTED
Phase: 3
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/WebstreamModelTest.php`
Next step: Test create, getUrl, setMetadata
Notes: Webstream support

---

# LEGACY TESTING PLAN — Phase 4: Forms (Weeks 7-8)

## [MEDIUM] test T123 — Test Login Form validation
Status: NOT_STARTED
Phase: 4
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/forms/LoginFormTest.php`
Next step: Test username/password validation and CSRF
Notes: Auth entry point

## [MEDIUM] test T124 — Test AddUser Form validation
Status: NOT_STARTED
Phase: 4
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/forms/AddUserFormTest.php`
Next step: Test email, username uniqueness, password complexity, user type
Notes: User creation validation

## [MEDIUM] test T125 — Test AddShow forms
Status: NOT_STARTED
Phase: 4
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/forms/AddShowFormsTest.php`
Next step: Test AddShowWhat, AddShowWhen, AddShowRepeats, AddShowWho, AddShowStyle
Notes: Multi-step show creation

## [MEDIUM] test T126 — Test EditUser Form validation
Status: NOT_STARTED
Phase: 4
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/forms/EditUserFormTest.php`
Next step: Test profile editing, password change, permission changes
Notes: User management

## [LOW] test T127 — Test Preferences Forms
Status: NOT_STARTED
Phase: 4
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/forms/PreferencesFormsTest.php`
Next step: Test GeneralPreferences, LiveStreamingPreferences, StreamSetting
Notes: System settings

---

# LEGACY TESTING PLAN — Phase 5: Auth & Security (Weeks 8-9)

## [CRITICAL] test T128 — Test Auth Model authentication
Status: NOT_STARTED
Phase: 5
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/AuthModelTest.php`
Next step: Test getAuthAdapter, authenticate (success/fail), logout
Notes: Core authentication

## [CRITICAL] test T129 — Test ACL Plugin access control
Status: NOT_STARTED
Phase: 5
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/plugins/AclPluginTest.php`
Next step: Test guest/host/admin/superadmin access levels, 403 responses
Notes: Authorization framework

## [MEDIUM] test T130 — Test Custom Validators
Status: NOT_STARTED
Phase: 5
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/validators/CustomValidatorsTest.php`
Next step: Test UserNameValidate, NotDemoValidate, ConditionalNotEmpty
Notes: Input validation

---

# LEGACY TESTING PLAN — Phase 6: Controllers — Core (Weeks 9-11)

## [HIGH] test T131 — Test LoginController
Status: NOT_STARTED
Phase: 6
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/controllers/LoginControllerTest.php`
Next step: Test indexAction (form display, login success/fail), logoutAction, passwordChangeAction
Notes: Auth controller

## [HIGH] test T132 — Test UserController
Status: NOT_STARTED
Phase: 6
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/controllers/UserControllerTest.php`
Next step: Test indexAction, addUserAction, editUserAction, removeUserAction, getUserDataAction
Notes: User management controller

## [HIGH] test T133 — Test ScheduleController
Status: NOT_STARTED
Phase: 6
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/controllers/ScheduleControllerTest.php`
Next step: Test indexAction, addShowAction, editShowAction, deleteShowAction, cancelShowAction, eventFeedAction
Notes: Schedule management controller

## [HIGH] test T134 — Test PlaylistController
Status: NOT_STARTED
Phase: 6
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/controllers/PlaylistControllerTest.php`
Next step: Test indexAction, newAction, editAction, deleteAction, addItemAction
Notes: Playlist management controller

## [HIGH] test T135 — Test LibraryController
Status: NOT_STARTED
Phase: 6
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/controllers/LibraryControllerTest.php`
Next step: Test indexAction, uploadAction, editFileMdAction, deleteAction, getFileMetadataAction
Notes: File library controller

## [MEDIUM] test T136 — Test ApiController
Status: NOT_STARTED
Phase: 6
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/controllers/ApiControllerTest.php`
Next step: Test dispatchMetadata, listAllFiles, status
Notes: API endpoints controller

---

# LEGACY TESTING PLAN — Phase 7: Integration & Edge Cases (Weeks 11-12)

## [HIGH] test T137 — Test Full Show Lifecycle
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/ShowLifecycleTest.php`
Next step: Test create → add content → start → complete flow
Notes: End-to-end show scenario

## [HIGH] test T138 — Test Repeating Show Instance Editing
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/ShowInstanceEditingTest.php`
Next step: Test editing single instance of recurring show
Notes: Complex recurring show logic

## [HIGH] test T139 — Test Show Recording Integration
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/ShowRecordingTest.php`
Next step: Test recording flow and history verification
Notes: Recording feature end-to-end

## [HIGH] test T140 — Test File Upload Flow
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/FileUploadFlowTest.php`
Next step: Test upload → metadata extraction → playlist addition
Notes: File workflow

## [MEDIUM] test T141 — Test Scheduling Conflicts
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/SchedulingConflictsTest.php`
Next step: Test overlapping shows prevention and rescheduling with conflicts
Notes: Conflict resolution

## [MEDIUM] test T142 — Test Timezone Edge Cases
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/TimezoneEdgeCasesTest.php`
Next step: Test DST transition, cross-timezone scheduling, negative offsets
Notes: Timezone handling edge cases

## [MEDIUM] test T143 — Test Permission Scenarios
Status: NOT_STARTED
Phase: 7
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/integration/PermissionScenariosTest.php`
Next step: Test host editing others' shows, guest restrictions, program manager rights
Notes: Authorization scenarios

---

# LEGACY TESTING PLAN — Phase 8: REST API Module (Weeks 12-13)

## [MEDIUM] test T144 — Test REST MediaController
Status: NOT_STARTED
Phase: 8
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/modules/rest/MediaControllerTest.php`
Next step: Test GET/POST/PUT/DELETE /media endpoints
Notes: REST API media management

## [MEDIUM] test T145 — Test REST PodcastController
Status: NOT_STARTED
Phase: 8
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/modules/rest/PodcastControllerTest.php`
Next step: Test GET/POST/PUT/DELETE /podcasts endpoints
Notes: REST API podcast management

## [LOW] test T146 — Test REST ShowImageController
Status: NOT_STARTED
Phase: 8
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/modules/rest/ShowImageControllerTest.php`
Next step: Test GET/POST show image endpoints
Notes: Show image API

---

# LEGACY TESTING PLAN — Phase 9: Formatters & Utilities (Weeks 13-14)

## [LOW] test T147 — Test Formatters
Status: NOT_STARTED
Phase: 9
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/formatters/FormattersTest.php`
Next step: Test LengthFormatter, BitrateFormatter, SamplerateFormatter, TimeFilledFormatter
Notes: Display formatting utilities

---

# LEGACY TESTING PLAN — Phase 10: Final Coverage & Polish (Weeks 14-15)

## [MEDIUM] test T148 — Generate coverage report and identify gaps
Status: NOT_STARTED
Phase: 10
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
Next step: Run full coverage analysis, document uncovered areas
Notes: Target: 80% total coverage

## [MEDIUM] test T149 — Write missing tests for coverage gaps
Status: NOT_STARTED
Phase: 10
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
Next step: Implement tests for identified uncovered code
Notes: Depends on T148

## [LOW] test T150 — Create performance tests
Status: NOT_STARTED
Phase: 10
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
Next step: Test large playlists (>1000 items), many repeating shows, library search stress
Notes: Performance baseline

## [LOW] test T151 — Document test helpers and create HOWTO
Status: NOT_STARTED
Phase: 10
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/README.md`, `legacy/tests/HOWTO.md`
Next step: Document helpers and create guide for adding new tests
Notes: Developer documentation

## [LOW] test T152 — Update TESTING.md with results
Status: NOT_STARTED
Phase: 10
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/TESTING.md`
Next step: Document final coverage metrics and testing approach
Notes: Project documentation

---

# API v2 COMPREHENSIVE TEST COVERAGE PLAN
# Target: 100% API external interface + database behavior coverage
# Purpose: Create test suite that will validate both current DRF and future FastAPI implementations

## [CRITICAL] test T153 — Create API test infrastructure base
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API v2 test foundation
Next step: Create conftest.py with fixtures for API testing (auth clients, model factories)
Notes: Base for all API tests. Must include: api_client (Api-Key auth), authenticated_client (session auth), admin_user, regular_user fixtures

## [CRITICAL] test T154 — Create User model factory for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core test data
Next step: Create model_bakery recipe for User with all roles (G, H, P, A)
Notes: Required for permission testing across all endpoints

## [CRITICAL] test T155 — Create File model factory for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage test data
Next step: Create model_bakery recipe for File with valid audio metadata
Notes: Required for storage and schedule module tests

## [CRITICAL] test T156 — Create Show/Instance/Days factories for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule test data
Next step: Create model_bakery recipes for Show, ShowInstance, ShowDays with proper relationships
Notes: Complex relationships needed for schedule tests

## [HIGH] test T157 — Create Playlist/Content factories for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule test data
Next step: Create model_bakery recipes for Playlist and PlaylistContent
Notes: Required for playlist CRUD and content management tests

## [HIGH] test T158 — Create SmartBlock factories for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule test data
Next step: Create model_bakery recipes for SmartBlock, SmartBlockContent, SmartBlockCriteria
Notes: Static and dynamic block types

## [HIGH] test T159 — Create Podcast factories for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts test data
Next step: Create model_bakery recipes for Podcast, PodcastEpisode, StationPodcast, ImportedPodcast
Notes: Including iTunes metadata fields

## [HIGH] test T160 — Create History model factories for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history test data
Next step: Create model_bakery recipes for PlayoutHistory, ListenerCount, LiveLog
Notes: Timestamp relationships required

## [HIGH] test T161 — Create Schedule factory for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule test data
Next step: Create model_bakery recipe for Schedule with cue_in/cue_out calculations
Notes: Most critical model - links files to show instances

## [HIGH] test T162 — Create Webstream factory for API tests
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule test data
Next step: Create model_bakery recipe for Webstream and WebstreamMetadata
Notes: Required for stream scheduling tests

# === CORE MODULE TESTS ===

## [HIGH] test T163 — Test Users LIST (GET /api/v2/users)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test LIST endpoint - verify response structure, pagination if present, field types
Notes: Must test: 200 OK, response schema matches UserSerializer, all expected fields present

## [HIGH] test T164 — Test Users CREATE (POST /api/v2/users)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test CREATE with valid data - verify user created, password hashed with MD5
Notes: Test: 201 Created, MD5 hash stored (not plaintext), all fields saved correctly

## [HIGH] test T165 — Test Users CREATE validation errors
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test CREATE with invalid data - duplicate username, invalid role, missing required fields
Notes: Test: 400 Bad Request, appropriate error messages, no DB record created

## [HIGH] test T166 — Test Users RETRIEVE (GET /api/v2/users/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test RETRIEVE existing user - verify all fields returned, password NOT in response
Notes: Critical: password field must never be exposed in API responses

## [HIGH] test T167 — Test Users RETRIEVE 404 for non-existent
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test RETRIEVE with invalid ID - verify 404 Not Found
Notes: Edge case handling

## [HIGH] test T168 — Test Users UPDATE (PUT /api/v2/users/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test full UPDATE - verify all fields updated, partial data rejected
Notes: PUT requires all fields (DRF behavior)

## [HIGH] test T169 — Test Users PARTIAL_UPDATE (PATCH /api/v2/users/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test partial update - verify only provided fields change, others unchanged
Notes: PATCH allows partial updates

## [HIGH] test T170 — Test Users DELETE (DELETE /api/v2/users/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test DELETE - verify 204 No Content, user removed from DB
Notes: Test cascade behavior if user owns resources

## [HIGH] test T171 — Test Users permissions (admin vs regular user)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test permission matrix: admin can CRUD all users, regular user can only view/update self
Notes: IsAdminOrOwnUser permission logic

## [MEDIUM] test T172 — Test Users LIST filtered by role
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core users
Next step: Test filtering users by role parameter if supported
Notes: Check query params (?role=H)

## [HIGH] test T173 — Test Preferences LIST (GET /api/v2/preferences)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core preferences
Next step: Test LIST preferences - verify key-value structure
Notes: Site preferences vs user preferences

## [HIGH] test T174 — Test Preferences CREATE (POST /api/v2/preferences)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core preferences
Next step: Test CREATE preference - verify saved to DB
Notes: Test both site and user-specific preferences

## [HIGH] test T175 — Test Preferences UPDATE (PATCH /api/v2/preferences/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core preferences
Next step: Test UPDATE preference value - verify change persisted
Notes: Stream settings stored as preferences

## [MEDIUM] test T176 — Test ServiceRegister LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core services
Next step: Test LIST service registers
Notes: Internal service registration tracking

## [MEDIUM] test T177 — Test ServiceRegister heartbeat/update
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core services
Next step: Test service registration update endpoint
Notes: Services register themselves with IP

## [MEDIUM] test T178 — Test UserToken LIST/CREATE/DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core tokens
Next step: Test full CRUD for UserToken (password reset tokens)
Notes: Token generation for password reset flow

## [MEDIUM] test T179 — Test LoginAttempt tracking
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core auth
Next step: Test login attempt recording and retrieval
Notes: Rate limiting data

## [MEDIUM] test T180 — Test CeleryTask LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core tasks
Next step: Test LIST celery tasks
Notes: Background task status tracking

## [MEDIUM] test T181 — Test ThirdPartyTrackReference LIST/CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core external
Next step: Test external track reference CRUD
Notes: Integration with external services

## [HIGH] test T182 — Test Info endpoint (GET /api/v2/info)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core public
Next step: Test info endpoint - verify station_name in response
Notes: No auth required (AllowAny)

## [HIGH] test T183 — Test Version endpoint (GET /api/v2/version)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core public
Next step: Test version endpoint - verify api_version format
Notes: No auth required (AllowAny)

## [HIGH] test T184 — Test StreamPreferences endpoint
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core stream
Next step: Test GET /api/v2/stream/preferences - verify all fields present
Notes: Computed from Preference model

## [HIGH] test T185 — Test StreamState endpoint
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API core stream
Next step: Test GET /api/v2/stream/state - verify boolean flags
Notes: Computed from Preference model

# === STORAGE MODULE TESTS ===

## [CRITICAL] test T186 — Test Files LIST (GET /api/v2/files)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test LIST files - verify all 50+ fields in response, proper typing
Notes: Largest model, critical for migration

## [CRITICAL] test T187 — Test Files LIST with filters (md5, genre)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test filtering: ?md5=xxx, ?genre=Soul, combined filters
Notes: Existing test covers this - verify and expand

## [CRITICAL] test T188 — Test Files CREATE (POST /api/v2/files)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test CREATE file with all metadata fields - verify saved correctly
Notes: ImportStatus transitions, filepath validation

## [CRITICAL] test T189 — Test Files RETRIEVE (GET /api/v2/files/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test RETRIEVE file - verify all metadata, computed fields
Notes: File metadata extraction result

## [CRITICAL] test T190 — Test Files UPDATE metadata
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test UPDATE file metadata - artist, title, etc.
Notes: Editable fields vs computed fields

## [CRITICAL] test T191 — Test Files DELETE (DELETE /api/v2/files/{id})
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test DELETE file - verify file removed from filesystem AND DB
Notes: Uses os.remove on storage path, test with mock

## [CRITICAL] test T192 — Test Files DELETE non-existent
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test DELETE with invalid ID - verify 404
Notes: Edge case

## [CRITICAL] test T193 — Test Files DOWNLOAD action (GET /api/v2/files/{id}/download)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test download endpoint - verify X-Accel-Redirect header for nginx
Notes: Custom action, critical for file serving

## [CRITICAL] test T194 — Test Files DOWNLOAD 404
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test download with non-existent file - verify 404
Notes: Edge case

## [HIGH] test T195 — Test Files permissions (owner vs admin)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test permission matrix: owner can edit own files, admin can edit all, others read-only
Notes: change_own_file, delete_own_file permissions

## [HIGH] test T196 — Test Files validation (invalid mime, size)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test CREATE with invalid data - verify 400 errors
Notes: File validation rules

## [HIGH] test T197 — Test Libraries LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage libraries
Next step: Test LIST libraries (track types)
Notes: cc_track_types table

## [HIGH] test T198 — Test Libraries CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage libraries
Next step: Test CREATE library with code, name, description
Notes: Track type definition

## [HIGH] test T199 — Test Libraries UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage libraries
Next step: Test UPDATE library - change description, enabled flag
Notes: Visibility settings

## [HIGH] test T200 — Test Libraries DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage libraries
Next step: Test DELETE library - verify cascade behavior with files
Notes: Check if files lose library reference


# === SCHEDULE MODULE TESTS ===

## [CRITICAL] test T201 — Test Shows LIST (GET /api/v2/shows)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test LIST shows - verify all fields, hosts relationship
Notes: Complex model with many-to-many hosts

## [CRITICAL] test T202 — Test Shows CREATE with hosts
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test CREATE show with hosts assigned - verify relationships created
Notes: Many-to-many through ShowHost

## [CRITICAL] test T203 — Test Shows CREATE with live auth
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test CREATE show with live_stream_user/pass - verify stored
Notes: Live streaming credentials

## [CRITICAL] test T204 — Test Shows CREATE with autoplaylist
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test CREATE show with autoplaylist_id - verify linked
Notes: Auto-playlist feature

## [CRITICAL] test T205 — Test Shows RETRIEVE with computed fields
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test RETRIEVE - verify live_enabled computed property
Notes: Computed from live_auth_registered + live_auth_custom

## [CRITICAL] test T206 — Test Shows UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test UPDATE show metadata - name, description, colors
Notes: Editable fields

## [CRITICAL] test T207 — Test Shows UPDATE hosts
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test UPDATE show hosts - add/remove hosts
Notes: Many-to-many relationship management

## [CRITICAL] test T208 — Test Shows DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test DELETE show - verify cascade to instances, days
Notes: Cascade behavior critical

## [CRITICAL] test T209 — Test Shows permissions (host can edit own)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule shows
Next step: Test permission: show host can edit show, non-host cannot
Notes: change_own_show permission

## [CRITICAL] test T210 — Test ShowDays LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule show-days
Next step: Test LIST show days - verify repeat patterns
Notes: Weekly, bi-weekly, monthly repeats

## [CRITICAL] test T211 — Test ShowDays CREATE (weekly repeat)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule show-days
Next step: Test CREATE show day with weekly repeat
Notes: RepeatKind.WEEKLY = 0

## [CRITICAL] test T212 — Test ShowDays CREATE (monthly repeat)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule show-days
Next step: Test CREATE show day with monthly repeat
Notes: RepeatKind.MONTHLY = 2

## [CRITICAL] test T213 — Test ShowDays UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule show-days
Next step: Test UPDATE repeat pattern, start time
Notes: Changing schedule pattern

## [CRITICAL] test T214 — Test ShowDays DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule show-days
Next step: Test DELETE show day - verify instances affected
Notes: Instance generation logic

## [CRITICAL] test T215 — Test ShowInstances LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule instances
Next step: Test LIST instances for a show
Notes: Generated instances from pattern

## [CRITICAL] test T216 — Test ShowInstances RETRIEVE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule instances
Next step: Test RETRIEVE instance - verify starts/ends, filled_time
Notes: Instance details

## [CRITICAL] test T217 — Test ShowInstances UPDATE (modified instance)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule instances
Next step: Test UPDATE instance - mark as modified, change description
Notes: modified_instance flag

## [CRITICAL] test T218 — Test ShowInstances DELETE (single instance)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule instances
Next step: Test DELETE single instance vs delete all following
Notes: Instance deletion behavior

## [CRITICAL] test T219 — Test ShowRebroadcasts LIST/CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule rebroadcasts
Next step: Test CRUD for rebroadcast schedules
Notes: Day offset and time

## [CRITICAL] test T220 — Test ShowHosts LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule hosts
Next step: Test LIST hosts for a show
Notes: Through relationship

## [CRITICAL] test T221 — Test ShowHosts CREATE (add host to show)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule hosts
Next step: Test CREATE show host relationship
Notes: Adding host to show

## [CRITICAL] test T222 — Test ShowHosts DELETE (remove host)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule hosts
Next step: Test DELETE show host
Notes: Removing host from show

## [CRITICAL] test T223 — Test Playlists LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlists
Next step: Test LIST playlists - verify length computed
Notes: Playlist metadata

## [CRITICAL] test T224 — Test Playlists CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlists
Next step: Test CREATE playlist with owner
Notes: Creator assignment

## [CRITICAL] test T225 — Test Playlists UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlists
Next step: Test UPDATE playlist name/description
Notes: Metadata editing

## [CRITICAL] test T226 — Test Playlists DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlists
Next step: Test DELETE playlist - verify contents deleted
Notes: Cascade behavior

## [CRITICAL] test T227 — Test Playlists permissions
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlists
Next step: Test owner can edit, others read-only
Notes: change_own_playlist permission

## [CRITICAL] test T228 — Test PlaylistContents LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist-contents
Next step: Test LIST contents of playlist - verify order
Notes: Position field for ordering

## [CRITICAL] test T229 — Test PlaylistContents CREATE (add file)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist-contents
Next step: Test CREATE content - add file to playlist
Notes: Kind.FILE = 0

## [CRITICAL] test T230 — Test PlaylistContents CREATE (add stream)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist-contents
Next step: Test CREATE content - add webstream to playlist
Notes: Kind.STREAM = 1

## [CRITICAL] test T231 — Test PlaylistContents CREATE (add block)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist-contents
Next step: Test CREATE content - add smart block to playlist
Notes: Kind.BLOCK = 2

## [CRITICAL] test T232 — Test PlaylistContents UPDATE (reorder)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist-contents
Next step: Test UPDATE content position - reorder playlist
Notes: Position field update

## [CRITICAL] test T233 — Test PlaylistContents DELETE (remove item)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist-contents
Next step: Test DELETE content from playlist
Notes: Removal, verify position recalculation

## [CRITICAL] test T234 — Test SmartBlocks LIST (static and dynamic)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-blocks
Next step: Test LIST smart blocks - verify kind field
Notes: Static vs Dynamic

## [CRITICAL] test T235 — Test SmartBlocks CREATE static
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-blocks
Next step: Test CREATE static smart block
Notes: Kind.STATIC = "static"

## [CRITICAL] test T236 — Test SmartBlocks CREATE dynamic
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-blocks
Next step: Test CREATE dynamic smart block
Notes: Kind.DYNAMIC = "dynamic"

## [CRITICAL] test T237 — Test SmartBlocks UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-blocks
Next step: Test UPDATE smart block
Notes: Metadata editing

## [CRITICAL] test T238 — Test SmartBlocks DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-blocks
Next step: Test DELETE smart block - verify contents/criteria deleted
Notes: Cascade

## [CRITICAL] test T239 — Test SmartBlockContents LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block-contents
Next step: Test LIST contents of static smart block
Notes: For static blocks only

## [CRITICAL] test T240 — Test SmartBlockContents CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block-contents
Next step: Test CREATE content in static block
Notes: Adding files to static block

## [CRITICAL] test T241 — Test SmartBlockCriteria LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block-criteria
Next step: Test LIST criteria for dynamic block
Notes: For dynamic blocks

## [CRITICAL] test T242 — Test SmartBlockCriteria CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block-criteria
Next step: Test CREATE criteria (genre=Jazz, etc.)
Notes: Dynamic block rules

## [CRITICAL] test T243 — Test SmartBlockCriteria UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block-criteria
Next step: Test UPDATE criteria condition/value
Notes: Modifying rules

## [CRITICAL] test T244 — Test SmartBlockCriteria DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block-criteria
Next step: Test DELETE criteria
Notes: Remove rule from dynamic block

## [CRITICAL] test T245 — Test Webstreams LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule webstreams
Next step: Test LIST webstreams
Notes: External streams

## [CRITICAL] test T246 — Test Webstreams CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule webstreams
Next step: Test CREATE webstream with URL
Notes: URL validation

## [CRITICAL] test T247 — Test Webstreams UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule webstreams
Next step: Test UPDATE webstream URL
Notes: Edit stream URL

## [CRITICAL] test T248 — Test Webstreams DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule webstreams
Next step: Test DELETE webstream
Notes: Remove stream

## [CRITICAL] test T249 — Test WebstreamMetadata LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule webstream-metadata
Next step: Test LIST metadata for scheduled streams
Notes: Liquidsoap data

## [CRITICAL] test T250 — Test Schedule LIST with filters
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test LIST with: ?starts_after=, ?starts_before=, ?overbooked=
Notes: Complex filtering existing test covers

## [CRITICAL] test T251 — Test Schedule LIST overbooked filter
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test ?overbooked=true/false filter
Notes: Items extending beyond show instance

## [CRITICAL] test T252 — Test Schedule CREATE (schedule file)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test CREATE schedule item with file
Notes: File scheduling

## [CRITICAL] test T253 — Test Schedule CREATE (schedule stream)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test CREATE schedule item with webstream
Notes: Stream scheduling

## [CRITICAL] test T254 — Test Schedule RETRIEVE with computed cue_out
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test RETRIEVE - verify cue_out_calculated when truncated by show end
Notes: Read serializer computes truncated cue_out

## [CRITICAL] test T255 — Test Schedule RETRIEVE with computed ends_at
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test RETRIEVE - verify ends_at_calculated when truncated
Notes: Read serializer computes truncated ends_at

## [CRITICAL] test T256 — Test Schedule UPDATE (reschedule)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test UPDATE schedule item - change time
Notes: Moving scheduled item

## [CRITICAL] test T257 — Test Schedule DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test DELETE schedule item
Notes: Unscheduling

## [CRITICAL] test T258 — Test Schedule permissions (host can edit own show)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule schedule
Next step: Test permission: show host can modify schedule
Notes: change_own_schedule permission


# === HISTORY MODULE TESTS ===

## [HIGH] test T259 — Test PlayoutHistory LIST with filters
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history playout
Next step: Test LIST with: ?instance_id=, ?starts_after=, ?starts_before=
Notes: Filter by show instance and time range

## [HIGH] test T260 — Test PlayoutHistory CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history playout
Next step: Test CREATE playout history entry
Notes: Record played item

## [HIGH] test T261 — Test PlayoutHistory RETRIEVE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history playout
Next step: Test RETRIEVE history entry
Notes: Get details

## [HIGH] test T262 — Test PlayoutHistoryTemplate LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history templates
Next step: Test LIST templates
Notes: History display templates

## [HIGH] test T263 — Test PlayoutHistoryTemplate CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history templates
Next step: Test CREATE template
Notes: Define template

## [HIGH] test T264 — Test ListenerCount LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history listener-counts
Next step: Test LIST listener counts - verify timestamp ordering
Notes: Aggregated listener data

## [HIGH] test T265 — Test LiveLog LIST with filters
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history live-log
Next step: Test LIST with: ?starts_after=, ?starts_before=, ?show_id=
Notes: Live broadcast events

## [HIGH] test T266 — Test LiveLog CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history live-log
Next step: Test CREATE live log entry
Notes: Record live event

## [MEDIUM] test T267 — Test MountName LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API history mounts
Next step: Test LIST mount names
Notes: Icecast mount points

# === PODCASTS MODULE TESTS ===

## [HIGH] test T268 — Test Podcasts LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts podcasts
Next step: Test LIST podcasts - verify all iTunes metadata
Notes: RSS feed metadata

## [HIGH] test T269 — Test Podcasts CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts podcasts
Next step: Test CREATE podcast with RSS URL
Notes: URL validation

## [HIGH] test T270 — Test Podcasts UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts podcasts
Next step: Test UPDATE podcast metadata
Notes: Edit podcast details

## [HIGH] test T271 — Test Podcasts DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts podcasts
Next step: Test DELETE podcast
Notes: Remove podcast

## [HIGH] test T272 — Test Podcasts sync action
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts podcasts
Next step: Test sync action - fetches latest episodes
Notes: Manual refresh

## [HIGH] test T273 — Test PodcastEpisodes LIST
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts episodes
Next step: Test LIST episodes for a podcast
Notes: Episode metadata

## [HIGH] test T274 — Test PodcastEpisodes CREATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts episodes
Next step: Test CREATE episode
Notes: Add episode manually

## [HIGH] test T275 — Test PodcastEpisodes UPDATE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts episodes
Next step: Test UPDATE episode
Notes: Edit episode

## [HIGH] test T276 — Test PodcastEpisodes DELETE
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts episodes
Next step: Test DELETE episode
Notes: Remove episode

## [HIGH] test T277 — Test StationPodcast LIST/GET
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts station
Next step: Test station podcast endpoints
Notes: Station's own podcast feed

## [HIGH] test T278 — Test ImportedPodcast LIST/GET
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API podcasts imported
Next step: Test imported podcast endpoints
Notes: Auto-imported episodes

# === AUTHENTICATION TESTS ===

## [CRITICAL] test T279 — Test session auth (login required)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API auth
Next step: Test that logged-in user can access protected endpoints
Notes: Standard DRF session auth

## [CRITICAL] test T280 — Test Api-Key auth (service token)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API auth
Next step: Test that service can auth with Api-Key header
Notes: IsSystemTokenOrUser permission

## [CRITICAL] test T281 — Test no auth returns 403
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API auth
Next step: Test that unauthenticated requests are rejected
Notes: 403 Forbidden

## [CRITICAL] test T282 — Test invalid Api-Key returns 403
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API auth
Next step: Test that invalid token is rejected
Notes: IsSystemTokenOrUser rejects bad tokens

## [CRITICAL] test T283 — Test public endpoints (info, version)
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API auth
Next step: Test that info/version don't require auth
Notes: AllowAny permission

# === EDGE CASE & INTEGRATION TESTS ===

## [CRITICAL] test T284 — Test ReadWriteSerializerMixin behavior
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule serializers
Next step: Test that Schedule GET vs POST use different serializers
Notes: Read excludes cue_out, write allows it

## [CRITICAL] test T285 — Test schedule overbooked detection
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule logic
Next step: Test that item extending beyond show instance is marked overbooked
Notes: Business logic

## [CRITICAL] test T286 — Test show instance generation from pattern
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule logic
Next step: Test that show days generate instances correctly
Notes: Celery task or model method

## [HIGH] test T287 — Test playlist length calculation
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule playlist
Next step: Test that playlist length is computed from contents
Notes: Computed field

## [HIGH] test T288 — Test smart block dynamic query
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API schedule smart-block
Next step: Test that dynamic block criteria generate correct file query
Notes: SQL generation from criteria

## [HIGH] test T289 — Test file unique together constraint
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage files
Next step: Test that duplicate filepath+md5 is rejected
Notes: UniqueConstraint

## [HIGH] test T290 — Test cascade deletes
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API relations
Next step: Test various cascade behaviors (show->instances, playlist->contents)
Notes: Data integrity

## [HIGH] test T291 — Test pagination if present
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API pagination
Next step: Test LIST endpoints with large datasets - verify pagination
Notes: ?page=, ?limit= params

## [MEDIUM] test T292 — Test concurrent edits
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API concurrency
Next step: Test that concurrent edits don't corrupt data
Notes: Transaction isolation

## [MEDIUM] test T293 — Test large payload handling
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API performance
Next step: Test LIST with 1000+ items - verify reasonable response time
Notes: Performance baseline

## [MEDIUM] test T294 — Test file metadata extraction on upload
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage upload
Next step: Test that uploaded file triggers metadata extraction
Notes: Celery task integration

## [MEDIUM] test T295 — Test replaygain calculation
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API storage analysis
Next step: Test that analyzer computes replaygain for files
Notes: Audio analysis

## [LOW] test T296 — Test API version compatibility
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API versioning
Next step: Test that /api/v2/ prefix is required
Notes: URL routing

## [LOW] test T297 — Test CORS headers
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API security
Next step: Test CORS headers for browser clients
Notes: Cross-origin requests

## [LOW] test T298 — Test rate limiting
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API security
Next step: Test rate limiting on auth endpoints
Notes: DRF throttling


# === TEST DOCUMENTATION & INTEGRATION ===

## [HIGH] test T299 — Create API test fixtures documentation
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test docs
Next step: Document all fixtures in conftest.py with usage examples
Notes: README for API test suite

## [HIGH] test T300 — Create API test run documentation
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test docs
Next step: Document how to run tests: cd app/api && uv run pytest
Notes: Include coverage reporting

## [HIGH] test T301 — Create API contract test guide
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test docs
Next step: Document contract test philosophy for FastAPI migration
Notes: Tests must pass on both DRF and FastAPI

## [HIGH] test T302 — Verify existing tests still pass
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test baseline
Next step: Run current tests: cd app/api && uv run pytest -v
Notes: Ensure no regressions before adding new tests

## [HIGH] test T303 — Set up API test coverage reporting
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test coverage
Next step: Configure pytest-cov for API tests: --cov=api --cov-report=html
Notes: Track coverage progress toward 100%

## [MEDIUM] test T304 — Create API test troubleshooting guide
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test docs
Next step: Document common issues: DB setup, auth fixtures, model_bakery
Notes: Developer onboarding

## [MEDIUM] test T305 — Create mock utilities for external services
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test utils
Next step: Create mocks for: file storage, podcast RSS fetch, email
Notes: Isolate external dependencies

## [MEDIUM] test T306 — Create parameterized test examples
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test patterns
Next step: Create examples using @pytest.mark.parametrize for permissions
Notes: DRY test code

## [MEDIUM] test T307 — Create API test performance benchmarks
Status: NOT_STARTED
Created: 2026-04-07T20:00:00Z
Last worked: 2026-04-07T20:00:00Z
Scope: API test performance
Next step: Add timing assertions to critical endpoints
Notes: Baseline for FastAPI comparison

# === SUMMARY ===
# Total API v2 test tasks: 155 tasks (T153-T307)
# 
# Breakdown by component:
# - Infrastructure (T153-T162): 10 tasks - fixtures, factories, base classes
# - Core module (T163-T184): 22 tasks - users, preferences, auth, public endpoints
# - Storage module (T185-T200): 16 tasks - files, libraries with download action
# - Schedule module (T201-T258): 58 tasks - shows, instances, playlists, smart blocks, schedule
# - History module (T259-T267): 9 tasks - playout history, listener counts, live log
# - Podcasts module (T268-T278): 11 tasks - podcasts, episodes, station/imported
# - Auth tests (T279-T283): 5 tasks - session, api-key, permissions
# - Edge cases (T284-T298): 15 tasks - serializers, validation, pagination, performance
# - Documentation (T299-T307): 9 tasks - docs, guides, benchmarks
#
# Critical path (must have for FastAPI migration):
# T153-T162: Infrastructure
# T163-T168, T173-T184: Core endpoints
# T186-T194: Files (especially T193 download)
# T201-T258: Schedule (complex relationships)
# T279-T283: Authentication
# T284: ReadWriteSerializerMixin behavior
#
# Estimated implementation time: 2-3 weeks full-time
# Test files to create: ~25-30 new test files
# Total test functions: ~200-250 test cases
