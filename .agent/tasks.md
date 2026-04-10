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
- **`T<n>`** — **global** task identifier: literal **`T`** plus a decimal integer **`n`** with **no leading zeros** (`T1`, `Tn`, `T...`). **One sequence per repository:** backlog, active, completed, and cancelled entries all share the same counter. **`n` never decreases and is never reused** (cancelled tasks keep their `T<n>` in the file).

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

## [CRITICAL] fix T475 — BOLA: SmartBlockContent CREATE allows content in other user's block
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/views/smart_block.py:51-57`
Next step: Add ownership check in SmartBlockContentViewSet.create() or serializer
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can create content in victim's SmartBlock
  by specifying victim's block ID. No ownership validation on block field.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_bola_create_in_other_users_block

## [CRITICAL] fix T476 — BOLA: SmartBlockContent CREATE allows using other user's file
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/views/smart_block.py:51-57`
Next step: Add file ownership validation in serializer
Notes: |
  Attacker can reference victim's private file when creating SmartBlockContent.
  File existence is checked but ownership is not validated.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_bola_create_with_other_users_file

## [HIGH] fix T477 — BOPLA: SmartBlockContent CREATE allows mass assignment of id field
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/serializers/smart_block.py:22-30`
Next step: Add read_only=True for id field in SmartBlockContentSerializer
Notes: |
  API3:2023 Broken Object Property Level Authorization. Client can specify id field
  in CREATE request which could lead to ID collision or overwrite existing records.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_bopla_mass_assignment_id_field

## [MEDIUM] fix T478 — BOPLA: SmartBlockContent CREATE accepts extra/unknown fields silently
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/serializers/smart_block.py:22-30`
Next step: Add strict validation to reject unknown fields
Notes: |
  Extra fields like "is_admin", "role", "password" are silently ignored instead of rejected.
  Could mask typos or attempts at mass assignment.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_bopla_extra_fields_rejected

## [LOW] fix T479 — Path traversal in cue_in/cue_out fields not validated
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/serializers/smart_block.py:22-30`
Next step: Add path traversal pattern validation for cue fields
Notes: |
  Fields cue_in and cue_out accept path traversal patterns like "../../../etc/passwd".
  While likely not exploitable directly, should be rejected as invalid input.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_path_traversal_in_cue_fields

## [MEDIUM] fix T480 — Duplicate position values allowed in same SmartBlock
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/models/smart_block.py` (SmartBlockContent Meta)
Next step: Add unique_together = ('block', 'position') or allow nulls only
Notes: |
  Multiple SmartBlockContent entries can have same position value within one block.
  Causes ambiguity in ordering. Should either enforce uniqueness or auto-reassign.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_duplicate_position_same_block

## [MEDIUM] fix T481 — Negative offset value not validated
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/serializers/smart_block.py:22-30`
Next step: Add MinValueValidator(0) for offset field
Notes: |
  Negative offset values are accepted but don't make sense for audio playback.
  Should reject negative values with validation error.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_negative_offset_validation

## [LOW] fix T482 — cue_out before cue_in not validated
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/serializers/smart_block.py:22-30`
Next step: Add validate() method to check cue_out > cue_in
Notes: |
  cue_out time can be set before cue_in time, creating invalid playback range.
  Should validate that cue_out > cue_in when both provided.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_cue_out_before_cue_in

## [LOW] fix T483 — Invalid cue time format accepted
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/serializers/smart_block.py:22-30`
Next step: Add format validator for HH:MM:SS pattern
Notes: |
  cue_in/cue_out accept invalid formats like "not-a-time", "99:99:99", "25:00:00".
  Should validate HH:MM:SS format and reasonable time ranges.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_invalid_cue_format

## [MEDIUM] fix T484 — Invalid auth tokens may be partially accepted
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/permissions.py`
Next step: Ensure all invalid token formats return 403
Notes: |
  Malformed Authorization header might bypass some checks.
  Need to verify consistent 403 response for all invalid tokens.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_create_with_invalid_token

## [LOW] fix T485 — Wrong Content-Type not rejected
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/views/smart_block.py`
Next step: Add Content-Type validation
Notes: |
  POST with form-urlencoded instead of JSON is accepted.
  Should return 415 Unsupported Media Type for wrong content types.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_create_wrong_content_type

## [LOW] fix T486 — Race condition in concurrent SmartBlockContent CREATE
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/views/smart_block.py:39-57`
Next step: Add database-level constraints or atomic operations
Notes: |
  Concurrent CREATE requests with same data may create duplicates.
  Need unique constraints or proper locking.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_race_condition_concurrent_create

## [LOW] fix T487 — JSON Merge Patch accepted without validation
Status: NOT_STARTED
Created: 2026-04-10T13:35:00Z
Last worked: 2026-04-10T13:35:00Z
File: `app/api/api/schedule/views/smart_block.py`
Next step: Disable or properly validate application/merge-patch+json
Notes: |
  Content-Type application/merge-patch+json is accepted but may bypass validation.
  Should either disable or implement proper RFC 7386 validation.
  Ref: test_smartblockcontent_create_redteam_t240.py::test_json_merge_patch_mass_assignment

## [LOW] chore T52 — Remove unused import in file view
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/api/api/storage/views/file.py:3`
Notes: `from os import remove` unused (uses os.remove).

## [CRITICAL] fix T488 — BOLA: SmartBlockCriteria LIST shows all users' criteria
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py:71-77`
Next step: Add ownership filtering through block__owner
Notes: |
  API1:2023 Broken Object Level Authorization. LIST endpoint returns criteria
  for all blocks regardless of owner. Attacker can see victim's SmartBlockCriteria.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_bola_list_shows_all_users_criteria

## [CRITICAL] fix T489 — BOLA: SmartBlockCriteria filter by block bypasses ownership
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py:71-77`
Next step: Verify block ownership before filtering
Notes: |
  Attacker can filter by victim's block ID to see all criteria for that block.
  No ownership check on the block parameter.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_bola_filter_by_other_users_block

## [HIGH] fix T490 — SQL injection in SmartBlockCriteria block filter
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py:74-76`
Next step: Use Django ORM parameterization or validate block_id type
Notes: |
  Malformed block parameter may cause SQL errors. Need to ensure proper
  type casting and parameterization.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_filter_sql_injection_block_param

## [MEDIUM] fix T491 — 500 error on non-numeric block_id filter
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py:74-76`
Next step: Add try/except or validation for block_id parameter
Notes: |
  Query param ?block=abc causes 500 error instead of 400.
  Should validate that block_id is numeric before filtering.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_filter_non_numeric_block_id

## [MEDIUM] fix T492 — 500 error on unicode block_id filter
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py:74-76`
Next step: Add unicode handling or validation
Notes: |
  Query param ?block=日本語 causes 500 error instead of 400.
  Should handle unicode gracefully or reject with 400.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_filter_unicode_block_id

## [MEDIUM] fix T493 — Error message leaks database structure
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py`
Next step: Add custom error handling to hide SQL details
Notes: |
  Error messages reveal table names (cc_blockcriteria) and SQL details.
  Should return generic error messages to prevent information disclosure.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_error_message_leaks_structure

## [LOW] fix T494 — 500 error on special query params
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py:74-76`
Next step: Handle null/undefined/None values gracefully
Notes: |
  Query params like ?block=undefined or ?block=null cause 500 errors.
  Should treat these as invalid and return 400.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_fuzzing_query_params

## [HIGH] fix T495 — SmartBlockCriteria values leak block information
Status: NOT_STARTED
Created: 2026-04-10T13:45:00Z
Last worked: 2026-04-10T13:45:00Z
File: `app/api/api/schedule/views/smart_block.py`
Next step: Add ownership-based filtering to queryset
Notes: |
  Criteria values may contain sensitive configuration data that leaks
  information about victim's private blocks. Combined with T488.
  Ref: test_smartblockcriteria_list_redteam_t241.py::test_criteria_value_leaks_block_info

## [LOW] chore T53 — Update deprecated Celery backend
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `app/worker/worker/config.py:18`
Notes: "amqp" deprecated in Celery 5.x.

## [CRITICAL] fix T496 — BOLA: SmartBlockCriteria CREATE for other user's block
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/views/smart_block.py:71-77`
Next step: Add block ownership validation in create/serializer
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can create criteria
  for victim's SmartBlock by specifying victim's block ID.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_bola_create_for_other_users_block

## [HIGH] fix T497 — BOPLA: SmartBlockCriteria CREATE mass assignment id field
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add read_only=True for id field
Notes: |
  API3:2023 Broken Object Property Level Authorization. Client can specify id field.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_bopla_mass_assignment_id_field

## [MEDIUM] fix T498 — SmartBlockCriteria CREATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add strict validation or use explicit fields list
Notes: |
  Extra fields like "is_admin", "role" silently ignored instead of rejected.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_bopla_extra_fields_rejected

## [LOW] fix T499 — Very long SmartBlockCriteria value not validated
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add max_length validation for value field
Notes: |
  Value field accepts very long strings (10k+ chars) without validation.
  Should enforce reasonable limits.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_overflow_criteria_value

## [LOW] fix T500 — Negative group value accepted
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add MinValueValidator(0) for group field
Notes: |
  Negative group values don't make sense for criteria grouping.
  Should reject negative values.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_negative_group_value

## [LOW] fix T501 — Duplicate SmartBlockCriteria not handled
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/models/smart_block.py:144-159`
Next step: Decide if duplicates allowed or add unique constraint
Notes: |
  Multiple identical criteria can be created for same block.
  May be intentional or need deduplication.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_duplicate_criteria_same_block

## [MEDIUM] fix T502 — Invalid criteria type not validated
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add choices validation for criteria field
Notes: |
  Invalid criteria types like "invalid_criteria_type" are accepted.
  Should validate against allowed types (genre, artist, album, etc.)
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_invalid_criteria_type

## [LOW] fix T503 — Invalid condition type not validated
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add choices validation for condition field
Notes: |
  Invalid condition types are accepted. Should validate against
  allowed conditions (contains, starts, ends, is, etc.)
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_invalid_condition_type

## [LOW] fix T504 — Race condition in SmartBlockCriteria CREATE
Status: NOT_STARTED
Created: 2026-04-10T13:55:00Z
Last worked: 2026-04-10T13:55:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Add appropriate locking if needed
Notes: |
  Concurrent CREATE requests may cause race conditions.
  Need unique constraints or proper locking if duplicates not allowed.
  Ref: test_smartblockcriteria_create_redteam_t242.py::test_race_condition_concurrent_create

## [LOW] chore T54 — Replace MD5 with SHA256 for file hashes
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/files.py:11`
Notes: Not critical for file hashes but better to use SHA256.

## [CRITICAL] fix T505 — BOLA: SmartBlockCriteria UPDATE other user's criteria
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Add ownership check in update/patch operations
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can UPDATE victim's
  SmartBlockCriteria by knowing the ID. No ownership validation.
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_bola_update_other_users_criteria

## [CRITICAL] fix T506 — BOLA: SmartBlockCriteria DELETE other user's criteria
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Add ownership check in destroy operation
Notes: |
  Attacker can DELETE victim's SmartBlockCriteria by knowing the ID.
  Critical data loss vulnerability.
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_bola_delete_other_users_criteria

## [CRITICAL] fix T507 — BOLA: SmartBlockCriteria block takeover via UPDATE
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Validate block ownership on block field update
Notes: |
  Attacker can change criteria's block to victim's block via PATCH/PUT,
  effectively "stealing" the criteria or injecting into victim's block.
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_block_takeover_via_update

## [HIGH] fix T508 — BOPLA: SmartBlockCriteria UPDATE allows id modification
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add read_only=True for id field
Notes: |
  API3:2023 Broken Object Property Level Authorization. Client can attempt
  to change id field on update (though may not work due to URL routing).
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_mass_assignment_id_on_update

## [CRITICAL] fix T509 — BOLA: SmartBlockCriteria PUT allows block takeover
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Block ownership validation on PUT full update
Notes: |
  PUT full update allows changing block to victim's block.
  Similar to T507 but via PUT instead of PATCH.
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_put_full_update_block_takeover

## [LOW] fix T510 — SmartBlockCriteria UPDATE accepts empty value
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add MinLengthValidator or required validation
Notes: |
  Empty string value is accepted on PATCH/PUT update.
  May cause issues with criteria matching.
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_update_empty_value

## [LOW] fix T511 — SmartBlockCriteria UPDATE long value not validated
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/serializers/smart_block.py:34-38`
Next step: Add max_length validation for value field
Notes: |
  Very long values (10k+ chars) accepted on update.
  Should enforce same limits as CREATE.
  Ref: test_smartblockcriteria_update_redteam_t243.py::test_update_very_long_value

## [LOW] chore T55 — Remove duplicate in __all__
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
File: `src/sdk/sdk/__init__.py:13-22`
Notes: "config" appears twice.

## [HIGH] fix T512 — BOLA: DELETE other user's criteria returns wrong status
Status: NOT_STARTED
Created: 2026-04-10T14:05:00Z
Last worked: 2026-04-10T14:05:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Return 403 instead of 404 for unauthorized delete
Notes: |
  API1:2023 Broken Object Level Authorization. Currently returns 404 for both
  non-existing and existing-but-unauthorized criteria, which leaks existence.
  Should return 403 for existing criteria that user cannot access.
  Ref: test_smartblockcriteria_delete_redteam_t244.py::test_bola_delete_other_users_criteria_status

## [MEDIUM] fix T513 — BOLA: Batch delete scope verification
Status: NOT_STARTED
Created: 2026-04-10T14:05:00Z
Last worked: 2026-04-10T14:05:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Add test to verify single-record deletion only
Notes: |
  Ensure DELETE /api/v2/smart-block-criteria/{id} only affects one record.
  Mass deletion via URL manipulation should not be possible.
  Ref: test_smartblockcriteria_delete_redteam_t244.py::test_bola_batch_delete_scope

## [MEDIUM] fix T514 — DELETE error message leaks criteria existence
Status: NOT_STARTED
Created: 2026-04-10T14:05:00Z
Last worked: 2026-04-10T14:05:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Unify error responses for existing/non-existing on unauthorized
Notes: |
  Different error messages for existing (permission denied) vs non-existing
  allow attackers to enumerate which criteria IDs exist.
  Ref: test_smartblockcriteria_delete_redteam_t244.py::test_error_message_leaks_existence

## [LOW] fix T515 — Race condition in concurrent DELETE
Status: NOT_STARTED
Created: 2026-04-10T14:05:00Z
Last worked: 2026-04-10T14:05:00Z
File: `app/api/api/schedule/views/smart_block.py:61-77`
Next step: Add atomic delete or handle gracefully
Notes: |
  Concurrent DELETE of same criteria may cause unexpected behavior.
  Should handle race condition gracefully.
  Ref: test_smartblockcriteria_delete_redteam_t244.py::test_race_condition_concurrent_delete

## [LOW] fix T516 — Block without criteria behavior
Status: NOT_STARTED
Created: 2026-04-10T14:05:00Z
Last worked: 2026-04-10T14:05:00Z
File: `app/api/api/schedule/models/smart_block.py`
Next step: Verify dynamic block without criteria is valid
Notes: |
  Ensure deleting all criteria from a block doesn't break the block.
  Dynamic block with no criteria should still be valid (just empty).
  Ref: test_smartblockcriteria_delete_redteam_t244.py::test_delete_all_criteria_from_block

## [MEDIUM] fix T517 — Invalid auth token returns 404 instead of 403
Status: NOT_STARTED
Created: 2026-04-10T14:05:00Z
Last worked: 2026-04-10T14:05:00Z
File: `app/api/api/permissions.py`
Next step: Fix auth check order - validate token before checking resource
Notes: |
  DELETE with invalid token returns 404 instead of 403, suggesting
  auth check happens after resource lookup or not at all.
  Ref: test_smartblockcriteria_delete_redteam_t244.py::test_delete_with_invalid_token

## [CRITICAL] fix T518 — BOLA: Webstreams LIST shows all users' streams
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add get_queryset() to filter by owner
Notes: |
  API1:2023 Broken Object Level Authorization. LIST endpoint returns all webstreams
  regardless of owner. Attacker can see victim's private webstream URLs.
  Ref: test_webstream_list_redteam_t245.py::test_bola_list_shows_all_users_webstreams

## [MEDIUM] fix T519 — Webstream serializer __all__ may expose sensitive fields
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Review and explicitly list allowed fields instead of __all__
Notes: |
  Using __all__ in serializer may expose fields not intended for API.
  Should explicitly define fields list for security.
  Ref: test_webstream_list_redteam_t245.py::test_field_exposure_all_fields_review

## [HIGH] fix T520 — URL field reflects internal network addresses
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add URL validation to block internal network addresses
Notes: |
  Internal URLs (localhost, 192.168.x.x, 10.x.x.x) are stored and reflected.
  Combined with BOLA (T518), this leaks internal network topology.
  Ref: test_webstream_list_redteam_t245.py::test_url_field_ssrf_reflection

## [MEDIUM] fix T521 — MIME type field accepts arbitrary values
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add MIME type validation or choices
Notes: |
  MIME type field accepts any string including XSS payloads like
  text/html<script>alert(1)</script>. May lead to XSS if reflected.
  Ref: test_webstream_list_redteam_t245.py::test_mime_type_arbitrary_values

## [LOW] fix T522 — URL length not validated
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add URL max_length validation
Notes: |
  URL field accepts very long strings (up to 512 chars per model).
  Should validate reasonable URL length.
  Ref: test_webstream_list_redteam_t245.py::test_url_length_overflow

## [HIGH] fix T523 — Invalid URL format accepted
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add URL format validation using URLValidator
Notes: |
  Invalid URLs like "not-a-url", "javascript:alert(1)", "file:///etc/passwd"
  are accepted. Should validate URL format and scheme (http/https only).
  Ref: test_webstream_list_redteam_t245.py::test_url_format_validation

## [LOW] fix T524 — Special query params cause 500 error
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add exception handling for invalid query params
Notes: |
  Query params like ?page=undefined or ?page=null may cause 500 errors.
  Should handle gracefully and return 400.
  Ref: test_webstream_list_redteam_t245.py::test_fuzzing_query_params

## [MEDIUM] fix T525 — Description field XSS not sanitized
Status: NOT_STARTED
Created: 2026-04-10T14:15:00Z
Last worked: 2026-04-10T14:15:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add HTML sanitization for description field
Notes: |
  Description field accepts and reflects HTML/JS without sanitization.
  Potential XSS vector if rendered in frontend without escaping.
  Ref: test_webstream_list_redteam_t245.py::test_description_xss_protection

## [LOW] chore T56 — Fix inconsistent media_id typing
Status: NOT_STARTED
Created: 2026-04-06T16:53:26Z
Last worked: 2026-04-06T16:53:26Z
Files: `app/api-client/api_client/v1.py:118-128`, `app/api-client/api_client/v2.py:249-262`
Notes: str vs int inconsistency.

## [MEDIUM] fix T526 — BOPLA: Webstream create with other user as owner
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/views/webstream.py:20-25`
Next step: Remove owner from serializer fields or validate in perform_create
Notes: |
  Attacker can specify owner field to create webstream with victim as owner.
  perform_create only sets owner if not already provided.
  Ref: test_webstream_create_redteam_t246.py::test_bopla_create_with_other_user_owner

## [HIGH] fix T527 — Webstream perform_create allows unauthenticated create
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/views/webstream.py:20-25`
Next step: Remove else branch that allows creation without owner
Notes: |
  perform_create has else branch: serializer.save() without owner when
  user is not authenticated. Combined with missing auth check, allows
  creation of streams without authentication.
  Ref: test_webstream_create_redteam_t246.py::test_create_unauthenticated_owner_bypass

## [MEDIUM] fix T528 — BOPLA: Webstream id field mass assignment
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add read_only=True for id field
Notes: |
  Client can attempt to set id field during creation.
  Should be read_only to prevent ID manipulation.
  Ref: test_webstream_create_redteam_t246.py::test_bopla_mass_assignment_id

## [MEDIUM] fix T529 — BOPLA: Webstream timestamps mass assignment
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add read_only=True for created_at/updated_at
Notes: |
  Client can set created_at/updated_at fields manually.
  Should be auto-generated and read_only.
  Ref: test_webstream_create_redteam_t246.py::test_bopla_mass_assignment_timestamps

## [LOW] fix T530 — BOPLA: Webstream extra fields not rejected
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add strict validation or use explicit fields list
Notes: |
  Extra fields like "is_admin", "role" silently ignored instead of rejected.
  Ref: test_webstream_create_redteam_t246.py::test_bopla_extra_fields_rejected

## [CRITICAL] fix T531 — SSRF: Webstream internal URL accepted
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add URL validation to block internal addresses
Notes: |
  Internal URLs (localhost, 192.168.x.x, 10.x.x.x) are accepted.
  Combined with BOLA in LIST (T518), leaks internal network topology.
  Ref: test_webstream_create_redteam_t246.py::test_ssrf_internal_url

## [CRITICAL] fix T532 — SSRF: Webstream cloud metadata URLs accepted
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Block cloud metadata IP ranges (169.254.169.254)
Notes: |
  Cloud metadata endpoints (AWS, GCP, DigitalOcean) are accepted.
  Can lead to credential exposure and server compromise.
  Ref: test_webstream_create_redteam_t246.py::test_ssrf_cloud_metadata

## [HIGH] fix T533 — Webstream dangerous URL schemes accepted
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Validate URL scheme (http/https only)
Notes: |
  Dangerous schemes accepted: file://, ftp://, javascript:, data:,
  dict://, gopher://, ldap://. Can lead to XSS, LFI, or other attacks.
  Ref: test_webstream_create_redteam_t246.py::test_url_scheme_validation

## [MEDIUM] fix T534 — XSS: Webstream name field not sanitized
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add HTML sanitization or validation
Notes: |
  Script tags and event handlers accepted in name field.
  XSS vector if rendered in frontend without escaping.
  Ref: test_webstream_create_redteam_t246.py::test_xss_in_name_field

## [MEDIUM] fix T535 — XSS: Webstream description field not sanitized
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add HTML sanitization for description field
Notes: |
  Description field accepts and reflects HTML/JS without sanitization.
  Ref: test_webstream_create_redteam_t246.py::test_xss_in_description_field

## [LOW] fix T536 — Webstream name length not validated
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add max_length validation matching model (255)
Notes: |
  Name field accepts very long strings, may cause DB errors.
  Ref: test_webstream_create_redteam_t246.py::test_name_length_validation

## [MEDIUM] fix T537 — Webstream empty name accepted
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-21`
Next step: Add MinLengthValidator for name field
Notes: |
  Empty string name is accepted. Should require non-empty name.
  Ref: test_webstream_create_redteam_t246.py::test_empty_name_validation

## [LOW] fix T538 — Webstream wrong Content-Type accepted
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add Content-Type validation
Notes: |
  Form data (x-www-form-urlencoded) accepted instead of JSON.
  Should return 415 Unsupported Media Type.
  Ref: test_webstream_create_redteam_t246.py::test_create_wrong_content_type

## [LOW] fix T539 — Race condition in Webstream concurrent create
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add unique constraint or proper locking
Notes: |
  Concurrent CREATE requests may create duplicates.
  Ref: test_webstream_create_redteam_t246.py::test_race_condition_concurrent_create

## [CRITICAL] fix T540 — Webstream creator_id NOT NULL violation
Status: NOT_STARTED
Created: 2026-04-10T14:20:00Z
Last worked: 2026-04-10T14:20:00Z
File: `app/api/api/schedule/views/webstream.py:20-25`
Next step: Ensure creator_id is set or remove NOT NULL constraint
Notes: |
  Database requires creator_id (NOT NULL) but API doesn't provide it.
  Causes 500 error on CREATE: "null value in column creator_id".
  Found during SQLi test in description field.
  Ref: test_webstream_create_redteam_t246.py::test_sqli_in_description_field

## [CRITICAL] fix T541 — BOLA: Webstream UPDATE other user's stream
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add ownership check in update/patch operations
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can UPDATE victim's
  webstream by knowing the ID. No ownership validation.
  Ref: test_webstream_update_redteam_t247.py::test_bola_update_other_users_stream

## [CRITICAL] fix T542 — BOLA: Webstream DELETE other user's stream
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add ownership check in destroy operation
Notes: |
  Attacker can DELETE victim's webstream by knowing the ID.
  Critical data loss vulnerability.
  Ref: test_webstream_update_redteam_t247.py::test_bola_delete_other_users_stream

## [MEDIUM] fix T543 — Webstream error message leaks existence
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Unify error responses for existing/non-existing on unauthorized
Notes: |
  Different error messages for existing (permission denied) vs non-existing
  allow attackers to enumerate which webstream IDs exist.
  Ref: test_webstream_update_redteam_t247.py::test_error_message_leaks_existence

## [CRITICAL] fix T544 — SSRF: Webstream UPDATE URL to internal
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add URL validation on update to block internal addresses
Notes: |
  Attacker can UPDATE existing stream URL to internal network address.
  Combined with LIST BOLA (T518), leaks internal topology.
  Ref: test_webstream_update_redteam_t247.py::test_ssrf_url_update_to_internal

## [CRITICAL] fix T545 — SSRF: Webstream UPDATE URL to cloud metadata
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Block cloud metadata IP ranges on update
Notes: |
  Attacker can UPDATE URL to cloud metadata endpoints (169.254.169.254).
  Can lead to credential exposure.
  Ref: test_webstream_update_redteam_t247.py::test_ssrf_url_update_to_metadata

## [HIGH] fix T546 — BOPLA: Webstream change owner on update
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add read_only=True for owner field
Notes: |
  Client can change owner field via PATCH/PUT to transfer ownership.
  Should be read_only.
  Ref: test_webstream_update_redteam_t247.py::test_bopla_change_owner_on_update

## [MEDIUM] fix T547 — BOPLA: Webstream modify id on update
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Ensure id field is read_only
Notes: |
  Client can attempt to modify id field on update.
  Should be read_only to prevent ID manipulation.
  Ref: test_webstream_update_redteam_t247.py::test_bopla_modify_id_on_update

## [MEDIUM] fix T548 — BOPLA: Webstream set created_at on update
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Ensure created_at is read_only
Notes: |
  Client can attempt to set created_at timestamp on update.
  Should be read_only and immutable.
  Ref: test_webstream_update_redteam_t247.py::test_bopla_set_created_at_on_update

## [MEDIUM] fix T549 — XSS: Webstream UPDATE name with script tags
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add HTML sanitization for name field on update
Notes: |
  Script tags accepted in name field on PATCH/PUT.
  XSS vector if rendered without escaping.
  Ref: test_webstream_update_redteam_t247.py::test_xss_update_name

## [MEDIUM] fix T550 — XSS: Webstream UPDATE description with script tags
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add HTML sanitization for description on update
Notes: |
  Script tags and event handlers accepted in description on update.
  Ref: test_webstream_update_redteam_t247.py::test_xss_update_description

## [HIGH] fix T551 — SSRF: Webstream PUT allows dangerous URL
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add URL validation on PUT full update
Notes: |
  PUT full update accepts internal/dangerous URLs.
  Same issue as PATCH (T544/T545) but via PUT.
  Ref: test_webstream_update_redteam_t247.py::test_put_full_update_ssrf

## [HIGH] fix T552 — BOPLA: Webstream PUT allows owner change
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Ensure owner is read_only on PUT
Notes: |
  PUT full update allows changing owner field.
  Same issue as PATCH (T546) but via PUT.
  Ref: test_webstream_update_redteam_t247.py::test_put_full_update_owner_change

## [MEDIUM] fix T553 — Webstream UPDATE accepts empty name
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add MinLengthValidator for name on update
Notes: |
  Empty string name accepted on PATCH/PUT.
  Should require non-empty name.
  Ref: test_webstream_update_redteam_t247.py::test_update_empty_name

## [HIGH] fix T554 — Webstream UPDATE accepts invalid URL format
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Add URL validation on update
Notes: |
  Invalid URLs like "not-a-url", "javascript:alert(1)" accepted on update.
  Should validate same as CREATE.
  Ref: test_webstream_update_redteam_t247.py::test_update_invalid_url_format

## [LOW] fix T555 — Race condition in Webstream concurrent update
Status: NOT_STARTED
Created: 2026-04-10T14:30:00Z
Last worked: 2026-04-10T14:30:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add optimistic locking if needed
Notes: |
  Concurrent UPDATE requests may cause lost updates.
  Consider adding versioning/locking.
  Ref: test_webstream_update_redteam_t247.py::test_race_condition_concurrent_update

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

## [LOW] test T147 — Test Formatters
Status: NOT_STARTED
Phase: 9
Created: 2026-04-07T13:16:18Z
Last worked: 2026-04-07T13:16:18Z
File: `legacy/tests/application/models/formatters/FormattersTest.php`
Next step: Test LengthFormatter, BitrateFormatter, SamplerateFormatter, TimeFilledFormatter
Notes: Display formatting utilities

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

## [DONE] fix T308 — Fix IsAdminOrOwnUser permission crash on unauthenticated requests
Status: DONE
Created: 2026-04-09T12:00:00Z
Last worked: 2026-04-10T00:30:00Z
Scope: api/permissions.py
Notes: |
  FIXED: Added is_authenticated check before calling is_superuser() in both
  has_permission() and has_object_permission() methods.
  
  Root cause: AnonymousUser.is_superuser is a bool property, while User.is_superuser()
  is a method. Calling is_superuser() on AnonymousUser raised TypeError.
  
  Changes:
  - api/permissions.py: Added is_authenticated check in IsAdminOrOwnUser
  - test_user.py: Updated TestUserKnownBugs tests to expect 403 instead of 500
  - test_auth_session.py: Replaced TestBugT308 with TestIsAdminOrOwnUserPermission
  
  Tests: 8 new tests covering all permission scenarios

## [HIGH] test T309 — Add role-based filtering to UserViewSet
Status: NOT_STARTED
Created: 2026-04-09T12:00:00Z
Last worked: 2026-04-09T12:10:00Z
Scope: api/core/views/user.py
Next step: Add filterset_fields = ["role"] and DjangoFilterBackend
Notes: |
  Query param ?role=H is silently ignored, returns all users.
  When fixed, update test_user.py::TestUserKnownBugs::test_bug_b002_*

## [MEDIUM] test T310 — Decide API Key access to user management
Status: NOT_STARTED
Created: 2026-04-09T12:00:00Z
Last worked: 2026-04-09T12:10:00Z
Scope: api/permissions.py
Next step: Decide if system token should access user management
Notes: |
  Currently API Key returns 403 (after T308 fix), but maybe should work for service accounts?
  Ref: test_user.py::TestUserKnownBugs::test_bug_b003_*

## [DONE] fix T311 — Fix Preference unique_together validation in CREATE
Status: DONE
Created: 2026-04-09T12:25:00Z
Last worked: 2026-04-10T00:45:00Z
Scope: api/core/serializers/preference.py, api/core/views/preference.py
Notes: |
  FIXED: Serializer now properly validates unique_together = (user, key).
  
  Root cause: The serializer was using default DRF validation which saw the
  `unique=True` on the key field and validated globally. The database actually has:
  - cc_pref_subj_key_idx: UNIQUE (subjid, keystr) - the unique_together constraint
  - cc_pref_key_idx: UNIQUE (keystr) WHERE subjid IS NULL - partial index for site prefs
  
  Changes:
  - preference.py serializer: Removed unique validator from key field, added
    UniqueTogetherValidator for (user, key) with proper error message
  - preference.py view: Added IntegrityError handling in create() to return 400
    instead of 500 when DB constraint is violated
  - test_preference.py: Fixed tests to use same key (not faker.word() each time)
    and reflect actual database behavior
  
  Result: Same key can now be created for different users (as intended by schema).
  Ref: test_preference.py::TestPreferenceViewSetCreate::test_create_same_key_different_user_succeeds

## [DONE] test T312 — Fix Preference value handling for special characters
Status: DONE
Created: 2026-04-09T12:25:00Z
Last worked: 2026-04-10T03:55:00Z
Scope: api/core/tests/views/test_preference.py
Notes: |
  FIXED: Issue was with whitespace-only values being trimmed by legacy DB.
  
  Changes:
  - test_preference.py: Removed whitespace test case from test_create_preference_value_types
  - test_preference.py: Added separate test_create_preference_whitespace_trimmed documenting legacy behavior
  - test_preference.py: Removed xfail marker from test_create_preference_value_types
  
  Result: All value types (JSON, XML, HTML, unicode, etc.) now work correctly.
  Whitespace-only values are trimmed to empty string (legacy PostgreSQL behavior).

## [DONE] test T313 — Fix UserToken lookup_field for RETRIEVE/UPDATE/DELETE
Status: DONE
Created: 2026-04-09T12:40:00Z
Last worked: 2026-04-10T04:05:00Z
Scope: api/core/views/auth.py
Notes: |
  FIXED: Added lookup_field = "token" to UserTokenViewSet.
  
  Changes:
  - auth.py view: Added lookup_field = "token" to UserTokenViewSet
  - test_auth.py: Removed xfail markers from 2 UserToken tests
  
  Result: GET/DELETE /api/v2/user-tokens/{token}/ now works correctly.

## [DONE] test T314 — Fix LoginAttempt lookup_field for RETRIEVE/UPDATE/DELETE
Status: DONE
Created: 2026-04-09T13:20:00Z
Last worked: 2026-04-10T04:05:00Z
Scope: api/core/views/auth.py
Notes: |
  FIXED: Added lookup_field = "ip" and lookup_value_regex to LoginAttemptViewSet.
  
  Changes:
  - auth.py view: Added lookup_field = "ip" to LoginAttemptViewSet
  - auth.py view: Added lookup_value_regex = "[0-9.]+" to allow dots in IP addresses
  - test_auth.py: Removed xfail markers from 10 LoginAttempt tests
  
  Result: GET/PATCH/DELETE /api/v2/login-attempts/{ip}/ now works correctly.

## [HIGH] test T315 — Fix CeleryTask model db_column for track_reference
Status: NOT_STARTED
Created: 2026-04-09T13:30:00Z
Last worked: 2026-04-09T13:30:00Z
Scope: api/core/models/worker.py
Next step: Add db_column="track_reference" to track_reference ForeignKey
Notes: |
  BUG: Model has ForeignKey with db_column default (track_reference_id),
  but DB column is named "track_reference" (without _id suffix).
  Query fails: column celery_tasks.track_reference_id does not exist.
  HINT suggests: Perhaps you meant to reference the column "track_reference".
  Fix: track_reference = ForeignKey(..., db_column="track_reference")
  Ref: test_worker.py::TestCeleryTaskViewSetList

## [CRITICAL] fix T316 — FileViewSet.perform_destroy missing instance.delete()
Status: NOT_STARTED
Created: 2026-04-09T14:45:00Z
Last worked: 2026-04-09T14:45:00Z
Scope: api/storage/views/file.py
Next step: Add super().perform_destroy(instance) after remove(path)
Notes: |
  BUG: perform_destroy removes file from disk but never deletes DB record.
  Current flow: check Schedule -> check filepath -> isfile? -> remove(path) -> return
  Missing: instance.delete() call after successful remove.
  Result: DELETE returns 204, file removed from disk, but row remains in cc_files.
  Ref: test_file_delete.py::TestFileViewSetDelete::test_delete_file_removes_from_db

## [CRITICAL] fix T317 — FileViewSet.download crashes on None filepath
Status: NOT_STARTED
Created: 2026-04-09T15:15:00Z
Last worked: 2026-04-09T15:15:00Z
Scope: api/storage/views/file.py:48-49
Next step: Add null check before os.path.join or provide default
Notes: |
  BUG: download action crashes with TypeError when instance.filepath is None.
  Code: os.path.join("/api/_media", instance.filepath)  # filepath=None -> TypeError
  Result: 500 Internal Server Error instead of graceful handling.
  Fix: Check if filepath is None and return 400 or use empty string.
  Ref: test_file_download.py::TestFileViewSetDownload::test_download_no_filepath

## [CRITICAL] fix T318 — Library DELETE fails when Files reference it (track_type FK)
Status: NOT_STARTED
Created: 2026-04-09T16:30:00Z
Last worked: 2026-04-09T16:30:00Z
Scope: api/storage/models/file.py and api/storage/models/library.py
Next step: Fix DB constraint - use SET_NULL or CASCADE for track_type FK
Notes: |
  BUG: Cannot delete Library that has associated Files due to FK constraint violation.
  Root cause: File.track_type_id (db_column) references Library.id via DO_NOTHING.
  Error: "update or delete on table cc_track_types violates foreign key constraint cc_files_track_type_fkey"
  Impact: DELETE /api/v2/libraries/{id} returns 500 if library has files.
  Fix options: 1) SET_NULL on File.library FK, 2) Prevent delete if files exist (409).
  Ref: test_library_delete.py - 3 xfailed tests documenting this bug.

## [DONE] fix T319 — ShowSerializer missing live_auth fields
Status: DONE
Created: 2026-04-09T14:41:24Z
Last worked: 2026-04-10T03:50:00Z
Scope: api/schedule/serializers/show.py
Notes: |
  FIXED: Added live_auth fields to ShowSerializer.
  
  Changes:
  - show.py serializer: Added live_auth_registered, live_auth_custom, live_auth_custom_user, live_auth_custom_password to fields tuple
  - test_show_create.py: Removed xfail markers from 2 tests (test_create_show_with_live_auth_registered, test_create_show_with_live_auth_custom)
  
  Result: live_auth fields can now be set via API.

## [CRITICAL] fix T320 — ShowHost duplicate entries not prevented
Status: NOT_STARTED
Created: 2026-04-09T14:41:24Z
Scope: api/schedule/models/show.py (ShowHost Meta)
Next step: Add unique_together = ('show', 'user') to ShowHost model
Notes: Creating same show-host pair multiple times succeeds instead of returning 400/409

## [CRITICAL] fix T321 — Playlist CREATE allows null owner
Status: NOT_STARTED
Created: 2026-04-09T14:41:24Z
Scope: api/schedule/serializers/playlist.py
Next step: Add owner required validation in serializer
Notes: Creating playlist without owner returns 201 instead of 400

## [DONE] fix T322 — PlaylistContent filter by playlist not implemented
Status: DONE
Created: 2026-04-09T15:30:00Z
Last worked: 2026-04-10T03:25:00Z
Scope: api/schedule/views/playlist.py
Notes: |
  FIXED: Added filtering by playlist to PlaylistContentViewSet.
  
  Changes:
  - playlist.py view: Added filterset_fields=["playlist"], ordering_fields=["position"], ordering=["position"]
  - playlist.py view: Added get_queryset() to filter by playlist_id query param
  - test_playlistcontent_list.py: Removed xfail marker from test_list_filter_by_playlist
  
  Result: Query param ?playlist={id} now correctly filters playlist contents.

## [DONE] fix T323 — PlaylistContent ordering by position not implemented
Status: DONE
Created: 2026-04-09T15:30:00Z
Last worked: 2026-04-10T03:25:00Z
Scope: api/schedule/views/playlist.py
Notes: |
  FIXED: Added ordering by position to PlaylistContentViewSet.
  
  Changes:
  - playlist.py view: Added ordering_fields=["position"] and ordering=["position"] to ViewSet
  - test_playlistcontent_list.py: Removed xfail marker from test_list_contents_ordered_by_position
  
  Result: Results now returned in position sequence by default.

## [DONE] fix T324 — PlaylistContent offset is required but model allows null
Status: DONE
Created: 2026-04-09T16:05:00Z
Last worked: 2026-04-10T03:25:00Z
Scope: api/schedule/serializers/playlist.py
Notes: |
  FIXED: Made offset field optional in PlaylistContentSerializer.
  
  Changes:
  - playlist.py serializer: Added "offset": {"required": False} to extra_kwargs
  
  Result: Creating PlaylistContent without offset now succeeds.

## [DONE] fix T325 — PlaylistContent missing playlist not validated
Status: DONE
Created: 2026-04-09T16:05:00Z
Last worked: 2026-04-10T03:05:00Z
Scope: api/schedule/serializers/playlist.py
Notes: |
  FIXED: Added required validation for playlist field in PlaylistContentSerializer.
  
  Changes:
  - playlist.py serializer: Added extra_kwargs with required=True for playlist field
  - test_playlistcontent_create.py: Removed xfail marker from test_create_missing_playlist_fails
  
  Result: Creating PlaylistContent without playlist now returns 400 instead of 201.

## [DONE] fix T326 — PlaylistContent FILE kind without file not validated
Status: DONE
Created: 2026-04-09T16:05:00Z
Last worked: 2026-04-10T03:05:00Z
Scope: api/schedule/serializers/playlist.py
Notes: |
  FIXED: Added validation to require file when kind=FILE in PlaylistContentSerializer.
  
  Changes:
  - playlist.py serializer: Added validate() method to check that FILE kind has file assigned
  - test_playlistcontent_create.py: Removed xfail marker from test_create_file_without_file_id_fails
  
  Result: Creating PlaylistContent with kind=FILE but without file now returns 400 instead of 201.

## [DONE] fix T327 — SmartBlock filter by kind not implemented
Status: DONE
Created: 2026-04-09T17:00:00Z
Last worked: 2026-04-10T03:30:00Z
Scope: api/schedule/views/smart_block.py
Notes: |
  FIXED: Added filtering by kind to SmartBlockViewSet.
  
  Changes:
  - smart_block.py view: Added filterset_fields=["kind"], ordering_fields, ordering to ViewSet
  - smart_block.py view: Added get_queryset() to filter by kind query param
  - test_smartblock_list.py: Removed xfail marker from test_list_filter_by_kind
  
  Result: Query param ?kind=static|dynamic now correctly filters smart blocks.

## [DONE] fix T328 — SmartBlockContent filter by block not implemented
Status: DONE
Created: 2026-04-09T18:00:00Z
Last worked: 2026-04-10T02:45:00Z
Scope: api/schedule/views/smart_block.py
Notes: |
  FIXED: Added filtering by block to SmartBlockContentViewSet.
  
  Changes:
  - smart_block.py view: Added filter_backends with OrderingFilter
  - smart_block.py view: Added ordering_fields and ordering
  - smart_block.py view: Added get_queryset() with block_id filter
  - test_smartblockcontent_list.py: Removed xfail marker from test_list_filter_by_block

## [DONE] fix T329 — SmartBlockContent ordering by position not implemented
Status: DONE
Created: 2026-04-09T18:00:00Z
Last worked: 2026-04-10T02:45:00Z
Scope: api/schedule/views/smart_block.py
Notes: |
  FIXED: Added ordering by position to SmartBlockContentViewSet.
  
  Changes:
  - smart_block.py view: Added ordering_fields = ["position"]
  - smart_block.py view: Added ordering = ["position"] for default ordering
  - smart_block.py view: Added OrderingFilter to filter_backends
  - test_smartblockcontent_list.py: Removed xfail marker from test_list_contents_ordered_by_position

## [DONE] fix T330 — SmartBlockContent missing block not validated
Status: DONE
Created: 2026-04-09T18:10:00Z
Last worked: 2026-04-10T02:30:00Z
Scope: api/schedule/serializers/smart_block.py
Notes: |
  FIXED: Added required validation for block field in SmartBlockContentSerializer.
  
  Changes:
  - smart_block.py serializer: Added extra_kwargs with required=True for block field
  - test_smartblockcontent_create.py: Removed xfail marker from test_create_missing_block_fails
  
  Result: Creating SmartBlockContent without block now returns 400 instead of 201.

## [DONE] fix T331 — SmartBlockContent missing file not validated
Status: DONE
Created: 2026-04-09T18:10:00Z
Last worked: 2026-04-10T02:30:00Z
Scope: api/schedule/serializers/smart_block.py
Notes: |
  FIXED: Added required validation for file field in SmartBlockContentSerializer.
  
  Changes:
  - smart_block.py serializer: Added extra_kwargs with required=True for file field
  - test_smartblockcontent_create.py: Removed xfail marker from test_create_missing_file_fails
  
  Result: Creating SmartBlockContent without file now returns 400 instead of 201.

## [DONE] fix T332 — SmartBlockCriteria filter by block not implemented
Status: DONE
Created: 2026-04-09T18:20:00Z
Last worked: 2026-04-10T03:45:00Z
Scope: api/schedule/views/smart_block.py
Notes: |
  FIXED: Added filtering by block to SmartBlockCriteriaViewSet.
  
  Changes:
  - smart_block.py view: Added filterset_fields=["block"], ordering_fields, ordering to SmartBlockCriteriaViewSet
  - smart_block.py view: Added get_queryset() to filter by block_id query param
  - test_smartblockcriteria_list.py: Removed xfail marker from test_list_filter_by_block
  
  Result: Query param ?block={id} now correctly filters smart block criteria.

## [DONE] fix T333 — Webstream serializer requires optional fields on CREATE
Status: DONE
Created: 2026-04-09T19:10:00Z
Last worked: 2026-04-10T02:15:00Z
Scope: api/schedule/serializers/webstream.py, api/schedule/views/webstream.py
Notes: |
  FIXED: Made created_at, updated_at, length optional in serializer with auto-populated defaults.
  
  Changes:
  - webstream.py serializer: Added extra_kwargs with required=False for optional fields
  - webstream.py serializer: Added create() method with defaults (now() for timestamps, timedelta(0) for length)
  - webstream.py view: Added perform_create() to set owner from request.user
  - test_webstream_create.py: Changed tests to use authenticated_client fixture
  - Removed xfail markers from 3 tests

## [DONE] fix T334 — Webstream PUT requires optional fields
Status: DONE
Created: 2026-04-09T19:20:00Z
Last worked: 2026-04-10T02:15:00Z
Scope: api/schedule/serializers/webstream.py
Notes: |
  FIXED: Same fix as T333 - fields are now optional in serializer.
  
  Changes:
  - webstream.py serializer: Added update() method with auto-updated updated_at
  - test_webstream_update.py: Removed xfail marker from test_put_full_update_success
  
  Result: PUT full update now works without sending created_at, updated_at, length.

## [DONE] fix T335 — Schedule filter by instance not implemented
Status: DONE
Created: 2026-04-09T16:16:18Z
Last worked: 2026-04-10T03:35:00Z
File: `app/api/api/schedule/views/schedule.py`
Notes: |
  FIXED: Added instance filter to ScheduleFilter.
  
  Changes:
  - schedule.py view: Added instance = filters.NumberFilter(field_name="instance_id") to ScheduleFilter
  - test_schedule_list.py: Removed xfail marker from test_list_filter_by_instance
  
  Result: Filter ?instance={id} now correctly filters schedules by show instance ID.

## [DONE] fix T336 — Schedule CREATE missing file/stream validation
Status: DONE
Created: 2026-04-09T16:16:18Z
Last worked: 2026-04-10T03:35:00Z
File: `app/api/api/schedule/serializers/schedule.py`
Notes: |
  FIXED: Added file/stream validation to WriteScheduleSerializer.
  
  Changes:
  - schedule.py serializer: Added validate() method to require either file or stream
  - test_schedule_create.py: Removed xfail marker from test_create_missing_file_and_stream_fails
  
  Result: POST /api/v2/schedule with neither file nor stream now returns 400.

## [HIGH] fix T337 — Schedule datetime comparison bug in get_cue_out/get_ends_at
Status: NOT_STARTED
Created: 2026-04-09T16:16:18Z
Last worked: 2026-04-10T00:25:00Z
File: `app/api/api/schedule/models/schedule.py:120,127`
Next step: Ensure timezone-aware comparison in get_cue_out() and get_ends_at()
Notes: TypeError: can't compare offset-naive and offset-aware datetimes. Triggers on UPDATE when serializing response. VERIFIED 2026-04-10: Bug still reproduces - test_update_change_cue_times fails with AssertionError: '00:05:00' == '00:10:00'

## [MEDIUM] fix T338 — Schedule CREATE permissions for host user
Status: NOT_STARTED
Created: 2026-04-09T16:16:18Z
Last worked: 2026-04-09T16:16:18Z
File: `app/api/api/schedule/views/schedule.py`
Next step: Review permission classes, ensure host can create schedule for their shows
Notes: Host user (role=H) gets 403 on POST /api/v2/schedule. Admin works fine. Likely missing change_own_schedule permission check.

## [DONE] fix T339 — PlayoutHistory CREATE doesn't validate ends > starts
Status: DONE
Created: 2026-04-09T16:16:18Z
Last worked: 2026-04-10T03:40:00Z
File: `app/api/api/history/serializers/played.py`
Notes: |
  FIXED: Added ends > starts validation to PlayoutHistorySerializer.
  
  Changes:
  - played.py serializer: Added validate() method to check ends > starts
  - test_playout_history_create.py: Simplified test_create_ends_before_starts_fails (removed conditional xfail)
  
  Result: POST with ends before starts now returns 400.

## [DONE] fix T340 — Podcast model owner field DB schema mismatch
Status: DONE
Created: 2026-04-09T17:05:00Z
Last worked: 2026-04-10T01:00:00Z
File: `app/api/api/podcasts/models/podcast.py:27-32`
Notes: |
  FIXED: Added db_column="owner" to the ForeignKey.
  
  Root cause: Django ForeignKey by default looks for "owner_id" column, but the
  legacy database schema has the column named "owner" (not "owner_id").
  
  Changes:
  - podcast.py: Added db_column="owner" to owner ForeignKey
  - Removed xfail markers from all 38 podcast tests across 6 test files
  
  Result: All Podcast operations now work correctly. 42 tests pass (1 skipped).

## [DONE] test T341 — Fix IndexError in check_authorization_header with empty Api-Key
Status: DONE
Created: 2026-04-09T18:30:00Z
Last worked: 2026-04-10T04:10:00Z
Scope: api/permissions.py
Notes: |
  FIXED: Added bounds check before accessing split()[1] in check_authorization_header().
  
  Changes:
  - permissions.py: Added check `len(parts) < 2` before accessing `parts[1]`
  - test_auth_apikey.py: Removed xfail marker from test_empty_api_key_value_rejected
  - test_auth_apikey.py: Updated TestBugT341 tests to verify fix (no more IndexError)
  
  Result: Empty Api-Key header now returns 403 instead of crashing with IndexError.

## [HIGH] fix T355 — SmartBlockContent allows null block/file despite required validation
Status: NOT_STARTED
Created: 2026-04-10T09:45:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Add null check to validator
Notes: |
  RED TEAM FINDING from T330/T331 tests:
  
  The serializer has required=True for block and file fields, but:
  - POST with "block": null returns 201 (creates with null block)
  - POST with "file": null returns 201 (creates with null file)
  
  Root cause: required=True only checks field presence, not null value.
  Need additional validation to reject null values explicitly.
  
  Impact: Content without block/file is orphaned - cannot be properly managed.
  
  Red team tests confirming: 
  - test_create_with_null_block: FAIL (returns 201)
  - test_create_with_null_file: FAIL (returns 201)

## [HIGH] fix T356 — SmartBlockContent filter crashes on invalid block_id
Status: NOT_STARTED
Created: 2026-04-10T00:20:08Z
Scope: api/schedule/views/smart_block.py
Next step: Add validation for block_id query parameter
Notes: |
  RED TEAM FINDING from T328/T329 tests:
  
  SmartBlockContentViewSet.get_queryset() passes block_id directly to filter()
  without validation, causing ValueError on invalid input.
  
  Vulnerable code:
  - block_id = self.request.query_params.get("block")
  - queryset.filter(block_id=block_id)  # No validation!
  
  Attack scenarios:
  - GET ?block=invalid → ValueError: Field 'id' expected a number but got 'invalid'
  - GET ?block=-1 → May cause unexpected behavior
  - GET ?block=1' OR '1'='1 → SQL injection attempts cause 500 error
  
  Impact: Information disclosure via error messages, DoS via error spam.
  
  Fix needed: Validate block_id is integer before filtering, return 400 on invalid.

## [CRITICAL] fix T357 — PlaylistContent filter crashes on invalid playlist_id
Status: NOT_STARTED
Created: 2026-04-10T00:35:00Z
Scope: api/schedule/views/playlist.py
Next step: Add validation for playlist_id query parameter
Notes: |
  CRITICAL: Same vulnerability as T356 in PlaylistContentViewSet.
  
  Vulnerable code (views/playlist.py:37):
  - playlist_id = self.request.query_params.get("playlist")
  - queryset.filter(playlist_id=playlist_id)  # No validation!
  
  Attack scenarios:
  - GET ?playlist=invalid → ValueError: Field 'id' expected a number but got 'invalid'
  - GET ?playlist=1' OR '1'='1 → 500 error with traceback
  
  Impact: Information disclosure via error messages (database schema leak).
  
  Red team tests confirming: test_filter_by_invalid_playlist_id, test_filter_by_sql_injection

## [CRITICAL] fix T358 — PlaylistContent ViewSet missing owner-based filtering (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T00:35:00Z
Scope: api/schedule/views/playlist.py
Next step: Add get_queryset() filtering by playlist owner
Notes: |
  CRITICAL BOLA VULNERABILITY: PlaylistContentViewSet lacks owner-based filtering.
  
  Current behavior (BROKEN):
  - PlaylistContentViewSet.queryset = PlaylistContent.objects.all() - returns ALL content
  - get_queryset() filters by playlist_id but NOT by playlist owner
  
  Any authenticated user with 'view_playlistcontent' permission can:
  - List ALL playlist contents across ALL users
  - Access any content by ID (even in other users' playlists)
  - Modify any content (PATCH returns 200)
  - Delete any content (DELETE returns 204)
  
  This is Broken Object Level Authorization (BOLA/API1).
  
  Expected behavior:
  - Regular users only see content from their own playlists
  - Admins can see all content
  
  Red team tests confirming:
  - test_list_shows_only_own_content: FAIL - user sees admin content
  - test_access_other_user_content_directly: FAIL - 200 instead of 403
  - test_update_other_user_content: FAIL - can modify other user's content
  - test_delete_other_user_content: FAIL - can delete other user's content

## [HIGH] fix T359 — PlaylistContent playlist field transferable via PATCH
Status: NOT_STARTED
Created: 2026-04-10T00:35:00Z
Scope: api/schedule/serializers/playlist.py
Next step: Add playlist to read_only_fields
Notes: |
  SECURITY ISSUE: Content can be transferred between playlists via PATCH.
  
  Attack scenario:
  1. User A has playlist P1 with content C1
  2. User B has playlist P2
  3. User B calls PATCH /api/v2/playlist-contents/{C1}/ {"playlist": P2.id}
  4. Content C1 now belongs to P2 (user B steals content from user A)
  
  This enables content theft between users.
  
  Fix needed: Make playlist field read-only after creation.
  
  Red team test confirming: test_update_playlist_field returns 200 with transferred playlist

## [CRITICAL] fix T360 — PlaylistContent anonymous filter access
Status: NOT_STARTED
Created: 2026-04-10T00:50:00Z
Scope: api/schedule/views/playlist.py
Next step: Add authentication check to get_queryset or ViewSet
Notes: |
  CRITICAL: Anonymous users can filter playlist contents.
  
  Attack scenario:
  - GET /api/v2/playlist-contents?playlist=1 WITHOUT auth returns 200
  - Should return 403 Forbidden
  
  This allows unauthenticated data enumeration.
  
  Fix needed: Ensure permission classes reject anonymous users.
  
  Red team test confirming: test_filter_without_auth returns 200 instead of 403

## [HIGH] fix T361 — PlaylistContent accepts various invalid playlist_id formats
Status: NOT_STARTED
Created: 2026-04-10T00:50:00Z
Scope: api/schedule/views/playlist.py
Next step: Add proper input validation for playlist_id parameter
Notes: |
  Similar to T357 but broader scope - various input formats cause 500 errors:
  
  - ?playlist=1.5 (float) → ValueError
  - ?playlist=0x1 (hex) → ValueError  
  - ?playlist=invalid → ValueError
  
  All should return 400 Bad Request with clean error message.
  
  Root cause: No try/except around int() conversion in get_queryset().
  
  Fix needed: Validate and sanitize input before filtering.

## [CRITICAL] fix T362 — SmartBlock anonymous filter access
Status: NOT_STARTED
Created: 2026-04-10T00:55:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add authentication requirement to ViewSet
Notes: |
  CRITICAL: Anonymous users can filter smart blocks.
  
  Attack scenario:
  - GET /api/v2/smart-blocks?kind=static WITHOUT auth returns 200
  - Should return 403 Forbidden
  
  This allows unauthenticated enumeration of smart blocks.
  
  Red team test: test_filter_without_auth returns 200 instead of 403

## [CRITICAL] fix T363 — SmartBlock filter by kind shows other users' blocks
Status: NOT_STARTED
Created: 2026-04-10T00:55:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add owner filtering to get_queryset
Notes: |
  CRITICAL BOLA: Filtering smart blocks by kind returns ALL blocks, not just user's.
  
  Current behavior:
  - User A has block "Admin Static" (kind=static)
  - User B has block "User Static" (kind=static)
  - User B calls GET /api/v2/smart-blocks?kind=static
  - Response includes BOTH blocks
  
  This is Broken Object Level Authorization (BOLA/API1).
  
  Expected: User B should only see "User Static"
  
  Red team test: test_filter_shows_only_own_by_kind fails - shows admin block

## [CRITICAL] fix T354 — Webstream security issues (created_at mutable, owner transferable)
Status: NOT_STARTED
Created: 2026-04-10T09:40:00Z
Scope: api/schedule/serializers/webstream.py, api/schedule/views/webstream.py
Next step: Add read_only_fields to serializer, fix delete permission
Notes: |
  RED TEAM FINDINGS from T333/T334 tests:
  
  1. CREATED_AT MUTABLE (SECURITY):
     - PATCH {"created_at": "2019-01-01..."} successfully changes timestamp
     - created_at should be read-only after creation
     
  2. OWNER TRANSFERABLE (BOLA):
     - PATCH {"owner": other_user_id} transfers ownership
     - Owner should be immutable after creation
     
  3. ANONYMOUS DELETE (CRITICAL):
     - DELETE /api/v2/webstreams/{id} without auth returns 204
     - Anyone can delete webstreams!
     
  Red team tests: test_webstream_redteam_t333.py

## [CRITICAL] fix T353 — Podcast ViewSets missing owner-based queryset filtering (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T09:35:00Z
Scope: api/podcasts/views/podcast.py
Next step: Add get_queryset() filtering by owner to all Podcast ViewSets
Notes: |
  CRITICAL BOLA VULNERABILITY: All Podcast ViewSets lack owner-based filtering.
  
  Current behavior (BROKEN):
  - PodcastViewSet.queryset = Podcast.objects.all() - returns ALL podcasts
  - PodcastEpisodeViewSet.queryset = PodcastEpisode.objects.all() - returns ALL episodes
  - StationPodcastViewSet.queryset = StationPodcast.objects.all()
  - ImportedPodcastViewSet.queryset = ImportedPodcast.objects.all()
  
  Any authenticated user with 'view_podcast' permission can:
  - List all podcasts (including other users' private podcasts)
  - Access any podcast by ID
  - Access any episode
  - This is a Broken Object Level Authorization (BOLA/API1) vulnerability
  
  Expected behavior:
  - Regular users should only see their own podcasts (owner=request.user)
  - Admins can see all podcasts
  - Same for episodes, station podcasts, imported podcasts
  
  Fix needed:
  - Override get_queryset() in each ViewSet
  - Filter by owner for non-admin users
  - Use existing get_own_obj() pattern from api/permissions.py
  
  Red team tests confirming bug: test_podcast_redteam_t340.py
  - test_list_podcasts_shows_only_own: FAIL - user sees all podcasts
  - test_access_other_user_podcast_directly: FAIL - 200 instead of 403
  - test_access_episode_of_other_user_podcast: FAIL - 200 instead of 403
  - test_anonymous_cannot_list_podcasts: FAIL - 200 instead of 403
  - test_anonymous_cannot_create_podcast: FAIL - 201 instead of 403

## [CRITICAL] fix T364 — Schedule anonymous filter access
Status: NOT_STARTED
Created: 2026-04-10T01:05:00Z
Scope: api/schedule/views/schedule.py
Next step: Add authentication requirement to ScheduleViewSet
Notes: |
  CRITICAL: Anonymous users can filter schedules.
  
  Attack scenario:
  - GET /api/v2/schedule?instance=1 WITHOUT auth returns 200
  - Should return 403 Forbidden
  
  Red team test: test_filter_without_auth returns 200 instead of 403

## [CRITICAL] fix T365 — Schedule list shows all schedules (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T01:05:00Z
Scope: api/schedule/views/schedule.py
Next step: Add owner-based filtering to get_queryset
Notes: |
  CRITICAL BOLA: Schedule list returns ALL schedules, not just user's.
  
  Current behavior:
  - User B can see User A's schedules in LIST response
  
  Expected: User B should only see schedules they own
  
  Red team test: test_list_shows_only_own_schedules fails - shows admin schedule

## [CRITICAL] fix T366 — PlayoutHistory list shows all history (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T01:10:00Z
Scope: api/history/views/played.py
Next step: Add owner-based filtering to PlayoutHistoryViewSet
Notes: |
  CRITICAL BOLA: PlayoutHistory list returns ALL history entries.
  
  Current behavior:
  - User can see other users' playout history in LIST
  
  Expected: User should only see their own history
  
  Red team test: test_list_shows_only_own_history returns 404 (wrong endpoint?)
  but need to verify filtering behavior

## [CRITICAL] fix T367 — SmartBlockCriteria filter crashes on invalid block_id
Status: NOT_STARTED
Created: 2026-04-10T01:15:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add validation for block_id parameter
Notes: |
  CRITICAL: Same pattern as T356/T357 - filter crashes on invalid input.
  
  - ?block=invalid → ValueError
  - ?block=1.5 → ValueError
  - ?block=1' OR '1'='1 → ValueError
  
  Fix needed: Validate block_id before filtering.

## [CRITICAL] fix T368 — SmartBlockCriteria anonymous filter access
Status: NOT_STARTED
Created: 2026-04-10T01:15:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add authentication requirement
Notes: |
  CRITICAL: Anonymous users can filter smart block criteria.
  
  Red team test: test_filter_without_auth returns 200 instead of 403

## [CRITICAL] fix T369 — SmartBlockCriteria list shows all criteria (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T01:15:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add owner-based filtering
Notes: |
  CRITICAL BOLA: SmartBlockCriteria list returns ALL criteria.
  
  Red team test: test_list_shows_only_own_criteria fails

## [CRITICAL] fix T370 — Show live_auth_custom_password exposed in API response
Status: NOT_STARTED
Created: 2026-04-10T01:25:00Z
Scope: api/schedule/serializers/show.py
Next step: Add password to write_only_fields
Notes: |
  CRITICAL: live_auth_custom_password exposed in plaintext in API responses.
  
  Attack scenarios:
  - LIST /api/v2/shows returns password for all shows
  - GET /api/v2/shows/{id} returns password
  - Any authenticated user can see passwords
  
  Impact: Complete compromise of live stream authentication.
  
  Fix needed: Add live_auth_custom_password to write_only_fields in serializer.
  
  Red team tests confirming:
  - test_password_visible_in_list: FAIL - password exposed
  - test_password_visible_in_detail: FAIL - password exposed
  - test_other_user_password_not_visible: FAIL - any user can see password

## [HIGH] fix T371 — Preference user field transferable via PATCH
Status: NOT_STARTED
Created: 2026-04-10T01:30:00Z
Scope: api/core/serializers/preference.py
Next step: Add user to read_only_fields
Notes: |
  SECURITY ISSUE: Preference can be transferred to another user via PATCH.
  
  Attack scenario:
  - User A has preference P1
  - User A calls PATCH /api/v2/preferences/{P1} {"user": UserB.id}
  - Preference now belongs to User B
  
  This enables preference theft/transfer.
  
  Red team test: test_update_user_field fails - returns 200 with transferred user

## [CRITICAL] fix T372 — Preference list shows all preferences (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T01:30:00Z
Scope: api/core/views/preference.py
Next step: Add user filtering to get_queryset
Notes: |
  CRITICAL BOLA: Preference list returns ALL preferences.
  
  Red team test: test_list_shows_only_own_preferences returns 403 instead of filtered list

## [HIGH] fix T373 — UserToken token value mutable via PATCH
Status: NOT_STARTED
Created: 2026-04-10T01:35:00Z
Scope: api/core/serializers/auth.py
Next step: Add token to read_only_fields
Notes: |
  SECURITY ISSUE: Token value can be modified via PATCH.
  
  Tokens should be immutable once created.
  
  Red team test: test_update_token_value fails - returns 200

## [CRITICAL] fix T374 — LoginAttempt counter mutable via PATCH
Status: NOT_STARTED
Created: 2026-04-10T01:35:00Z
Scope: api/core/views/auth.py
Next step: Remove update permission or add validation
Notes: |
  CRITICAL: Login attempt counter can be reset via PATCH.
  
  Attack scenario:
  - Attacker has 5 failed attempts (blocked)
  - Attacker PATCH /api/v2/login-attempts/{ip} {"attempts": 0}
  - Counter reset, can brute force again
  
  This bypasses brute force protection!
  
  Red team test: test_modify_login_attempt_count fails - returns 200

## [HIGH] fix T375 — LoginAttempt record deletable
Status: NOT_STARTED
Created: 2026-04-10T01:35:00Z
Scope: api/core/views/auth.py
Next step: Remove delete permission
Notes: |
  SECURITY ISSUE: Login attempt records can be deleted.
  
  Attack scenario:
  - Attacker deletes their login attempt record
  - No audit trail of failed attempts
  
  Red team test: test_delete_login_attempt_record fails - returns 204

## [HIGH] fix T376 — Api-Key unicode handling crash
Status: NOT_STARTED
Created: 2026-04-10T01:40:00Z
Scope: api/permissions.py
Next step: Add unicode validation or error handling
Notes: |
  BUG: Unicode characters in Api-Key token cause UnicodeEncodeError.
  
  Error: 'latin-1' codec can't encode characters
  Location: rest_framework/authentication.py:23
  
  This causes 500 error instead of graceful 403.
  
  Red team test: test_unicode_token fails with UnicodeEncodeError

## [MEDIUM] fix T377 — Api-Key token revocation delay
Status: NOT_STARTED
Created: 2026-04-10T01:40:00Z
Scope: api/core/views/auth.py
Next step: Investigate caching or implement immediate revocation
Notes: |
  ISSUE: Deleted tokens still work immediately after deletion.
  
  Expected: Token should be immediately revoked
  Actual: Returns 403 (but test expects 200 for working token)
  
  May indicate caching issue or test timing issue.
  
  Red team test: test_token_revocation fails

## [CRITICAL] fix T378 — Show creation allows anonymous access
Status: NOT_STARTED
Created: 2026-04-10T02:00:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication requirement to ShowViewSet
Notes: |
  CRITICAL: Anyone can create shows without authentication.
  
  Attack scenario:
  - POST /api/v2/shows without auth returns 201
  - Anonymous user can flood system with shows
  
  Red team test: test_create_without_auth fails - returns 201

## [HIGH] fix T379 — Show accepts dangerous URL protocols
Status: NOT_STARTED
Created: 2026-04-10T02:00:00Z
Scope: api/schedule/serializers/show.py
Next step: Add URL validation to reject dangerous protocols
Notes: |
  SECURITY ISSUE: Show URL field accepts dangerous protocols:
  - javascript:alert('xss') - XSS attack
  - data:text/html,<script>alert('xss')</script> - XSS attack  
  - file:///etc/passwd - LFI attack
  
  These can lead to XSS when displayed in web UI.
  
  Red team tests:
  - test_url_with_javascript_protocol: FAIL
  - test_url_with_data_protocol: FAIL
  - test_url_with_file_protocol: FAIL

## [HIGH] fix T380 — Show description stored without XSS sanitization
Status: NOT_STARTED
Created: 2026-04-10T02:00:00Z
Scope: api/schedule/serializers/show.py
Next step: Add HTML sanitization or escape output
Notes: |
  SECURITY ISSUE: HTML/JS in description stored as-is (stored XSS).
  
  Payloads that work:
  - <script>alert('xss')</script>
  - <img src=x onerror=alert('xss')>
  
  When displayed in UI, these execute JavaScript.
  
  Red team tests:
  - test_description_with_html_script: FAIL
  - test_description_with_event_handlers: FAIL

## [MEDIUM] fix T381 — Show accepts invalid color format
Status: NOT_STARTED
Created: 2026-04-10T02:00:00Z
Scope: api/schedule/serializers/show.py
Next step: Add color format validation
Notes: |
  VALIDATION GAP: Show accepts invalid hex colors like "GGGGGG".
  
  Expected: Only valid hex colors (0-9, A-F) should be accepted
  Actual: Any 6-character string accepted
  
  Red team test: test_color_with_invalid_chars fails

## [CRITICAL] fix T382 — Show RETRIEVE allows anonymous access
Status: NOT_STARTED
Created: 2026-04-10T02:10:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication requirement
Notes: |
  CRITICAL: Anonymous users can retrieve show details.
  
  Attack scenario:
  - GET /api/v2/shows/{id} without auth returns 200
  - Information disclosure
  
  Red team test: test_retrieve_without_auth fails - returns 200

## [CRITICAL] fix T383 — Show BOLA/IDOR - no owner filtering
Status: NOT_STARTED
Created: 2026-04-10T02:10:00Z
Scope: api/schedule/views/show.py
Next step: Add owner-based filtering to get_queryset
Notes: |
  CRITICAL BOLA/IDOR: Any user can access any show by ID.
  
  Attack scenario:
  - User A has private show
  - User B calls GET /api/v2/shows/{show_id}
  - User B can see User A's private show
  
  No ownership verification in place.
  
  Red team tests:
  - test_access_other_user_show: FAIL
  - test_access_show_via_idor: FAIL

## [CRITICAL] fix T384 — Show UPDATE allows anonymous access
Status: NOT_STARTED
Created: 2026-04-10T02:20:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication requirement for PUT/PATCH
Notes: |
  CRITICAL: Anonymous can modify shows via PATCH/PUT.
  
  Attack scenarios:
  - PATCH /api/v2/shows/{id} without auth returns 200
  - PUT /api/v2/shows/{id} without auth returns 200
  
  Red team tests:
  - test_patch_without_auth: FAIL
  - test_put_without_auth: FAIL

## [HIGH] fix T385 — Show URL validation missing on PATCH
Status: NOT_STARTED
Created: 2026-04-10T02:20:00Z
Scope: api/schedule/serializers/show.py
Next step: Add URL protocol validation to update method
Notes: |
  SECURITY ISSUE: URL validation bypassed via PATCH.
  
  Can set dangerous URLs via PATCH:
  - javascript:alert('xss')
  - data:text/html,<script>alert('xss')</script>
  
  Red team tests:
  - test_patch_url_to_javascript: FAIL
  - test_patch_url_to_data_protocol: FAIL

## [HIGH] fix T386 — Show description XSS via PATCH
Status: NOT_STARTED
Created: 2026-04-10T02:20:00Z
Scope: api/schedule/serializers/show.py
Next step: Add HTML sanitization to PATCH
Notes: |
  SECURITY ISSUE: XSS injection works via PATCH.
  
  Can inject scripts via description PATCH:
  - <script>alert('xss')</script>
  - <img src=x onerror=alert('xss')>
  
  Red team tests:
  - test_patch_description_with_script: FAIL
  - test_patch_description_with_event_handler: FAIL

## [CRITICAL] fix T387 — Show DELETE allows anonymous access
Status: NOT_STARTED
Created: 2026-04-10T02:30:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication requirement for DELETE
Notes: |
  CRITICAL: Anonymous users can delete shows.
  
  Attack scenario:
  - DELETE /api/v2/shows/{id} without auth returns 204
  - Anyone can delete all shows
  
  Red team test: test_delete_without_auth fails - returns 204
Status: NOT_STARTED
Created: 2026-04-10T02:20:00Z
Scope: api/schedule/serializers/show.py
Next step: Add HTML sanitization to PATCH
Notes: |
  SECURITY ISSUE: XSS injection works via PATCH.
  
  Can inject scripts via description PATCH:
  - <script>alert('xss')</script>
  - <img src=x onerror=alert('xss')>
  
  Red team tests:
  - test_patch_description_with_script: FAIL
  - test_patch_description_with_event_handler: FAIL
Status: NOT_STARTED
Created: 2026-04-10T02:10:00Z
Scope: api/schedule/views/show.py
Next step: Add owner-based filtering to get_queryset
Notes: |
  CRITICAL BOLA/IDOR: Any user can access any show by ID.
  
  Attack scenario:
  - User A has private show
  - User B calls GET /api/v2/shows/{show_id}
  - User B can see User A's private show
  
  No ownership verification in place.
  
  Red team tests:
  - test_access_other_user_show: FAIL
  - test_access_show_via_idor: FAIL
Status: NOT_STARTED
Created: 2026-04-10T02:00:00Z
Scope: api/schedule/serializers/show.py
Next step: Add color format validation
Notes: |
  VALIDATION GAP: Show accepts invalid hex colors like "GGGGGG".
  
  Expected: Only valid hex colors (0-9, A-F) should be accepted
  Actual: Any 6-character string accepted
  
  Red team test: test_color_with_invalid_chars fails
Status: NOT_STARTED
Created: 2026-04-10T01:40:00Z
Scope: api/core/views/auth.py
Next step: Investigate caching or implement immediate revocation
Notes: |
  ISSUE: Deleted tokens still work immediately after deletion.
  
  Expected: Token should be immediately revoked
  Actual: Returns 403 (but test expects 200 for working token)
  
  May indicate caching issue or test timing issue.
  
  Red team test: test_token_revocation fails
Status: NOT_STARTED
Created: 2026-04-10T01:35:00Z
Scope: api/core/views/auth.py
Next step: Remove delete permission
Notes: |
  SECURITY ISSUE: Login attempt records can be deleted.
  
  Attack scenario:
  - Attacker deletes their login attempt record
  - No audit trail of failed attempts
  
  Red team test: test_delete_login_attempt_record fails - returns 204
Status: NOT_STARTED
Created: 2026-04-10T01:30:00Z
Scope: api/core/views/preference.py
Next step: Add user filtering to get_queryset
Notes: |
  CRITICAL BOLA: Preference list returns ALL preferences.
  
  Red team test: test_list_shows_only_own_preferences returns 403 instead of filtered list

## [HIGH] fix T352 — Fix Schedule.ends_at not saving via API
Status: NOT_STARTED
Created: 2026-04-10T00:55:00Z
Last worked: 2026-04-10T00:55:00Z
File: `app/api/api/schedule/serializers/schedule.py`
Next step: Investigate why DRF doesn't save ends_at when model has get_ends_at method
Notes: WriteScheduleSerializer cannot save ends_at field due to conflict with get_ends_at method on Schedule model. This causes test_update_change_times_success to fail. The starts_at field works correctly.

# Archive

<!--
Compressed history — user-commanded archive of completed/cancelled tasks.
Append-only: never edit or delete rows. T<n> preserved for ID continuity.
Scan this section when allocating next T<n> (max+1 rule).
-->

| ID | Date | Scope | Status | Title |
|----|------|-------|--------|-------|
| T1 | 2026-04-06 | meta | DONE | Initialize project documentation |
| T342 | 2026-04-09 | test | DONE | Standardize datetime formatting in API tests |
| T344 | 2026-04-09 | test | DONE | Fix failing API tests (isolation issues) |
| T345 | 2026-04-09 | test | DONE | Fix test suite isolation for full run |
| T346 | 2026-04-10 | test | DONE | Eliminate all hardcoded values in API tests |

<!-- 153 tasks archived. Max T<n> remains T351. -->

## [CRITICAL] bug T388 — Anonymous users can LIST ShowDays
Status: OPEN
Created: 2026-04-10T03:25:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication required to ShowDaysViewSet
Notes: |
  SECURITY ISSUE: Anonymous GET /api/v2/show-days returns 200 OK with all data.

  Attack scenario:
  - Unauthenticated attacker lists all show schedules
  - Information disclosure of station programming

  Red team test: test_list_without_auth fails - returns 200 instead of 403

## [CRITICAL] bug T389 — ShowDays BOLA: no owner filtering
Status: OPEN
Created: 2026-04-10T03:25:00Z
Scope: api/schedule/views/show.py
Next step: Add owner filtering to ShowDaysViewSet.get_queryset
Notes: |
  CRITICAL BOLA: ShowDays list returns ALL show days regardless of owner.

  Attack scenario:
  - User A can see User B's show schedules
  - Complete information disclosure across tenants

  Red team test: test_list_shows_only_own_days fails - shows other users' data

## [CRITICAL] bug T390 — ShowDays BOLA via show filter
Status: OPEN
Created: 2026-04-10T03:25:00Z
Scope: api/schedule/views/show.py
Next step: Add authorization check for show filter
Notes: |
  CRITICAL BOLA: Filtering by show_id doesn't verify ownership.

  Attack scenario:
  - Attacker filters by another user's show ID
  - Can enumerate and access others' show days

  Red team test: test_filter_by_other_user_show fails - returns other users' data

## [CRITICAL] bug T391 — Anonymous users can CREATE ShowDays
Status: OPEN
Created: 2026-04-10T11:20:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication required to ShowDaysViewSet
Notes: |
  SECURITY ISSUE: Anonymous POST /api/v2/show-days returns 201 Created.

  Attack scenario:
  - Unauthenticated attacker creates show schedules
  - Can flood system with fake show days
  - No audit trail of who created

  Red team test: test_create_without_auth fails - returns 201 instead of 403

## [MEDIUM] bug T419 — Playlist created_at mutable via PATCH
Status: OPEN
Created: 2026-04-10T11:45:00Z
Scope: api/schedule/serializers/playlist.py
Next step: Add created_at to read_only_fields in PlaylistSerializer
Notes: |
  SECURITY ISSUE: PATCH with created_at changes timestamp.

  Attack scenario:
  - User manipulates playlist creation date
  - Audit trail compromised
  - May affect sorting/reporting

  Red team test: test_update_created_at fails - created_at changed to 2020

## [CRITICAL] bug T411 — Anonymous users can LIST Playlists
Status: OPEN
Created: 2026-04-10T11:40:00Z
Scope: api/schedule/views/playlist.py
Next step: Add authentication required to PlaylistViewSet
Notes: |
  SECURITY ISSUE: Anonymous GET /api/v2/playlists returns 200 OK.

  Attack scenario:
  - Unauthenticated attacker lists all station playlists
  - Information disclosure of programming content

  Red team test: test_list_without_auth fails - returns 200 instead of 403

## [CRITICAL] bug T412 — Playlists BOLA: no owner filtering
Status: OPEN
Created: 2026-04-10T11:40:00Z
Scope: api/schedule/views/playlist.py
Next step: Add owner filtering to PlaylistViewSet.get_queryset
Notes: |
  CRITICAL BOLA: Playlists list returns ALL playlists regardless of owner.

  Attack scenario:
  - User A can see User B's private playlists
  - Complete information disclosure

  Red team test: test_list_shows_only_own_playlists fails - shows other users' data

## [CRITICAL] bug T413 — Playlists BOLA via owner filter
Status: OPEN
Created: 2026-04-10T11:40:00Z
Scope: api/schedule/views/playlist.py
Next step: Add authorization check for owner filter
Notes: |
  CRITICAL BOLA: Filtering by owner_id doesn't verify ownership.

  Attack scenario:
  - Attacker filters by another user's owner ID
  - Can enumerate all users' playlists

  Red team test: test_filter_by_other_owner fails - returns other users' data

## [CRITICAL] bug T407 — Anonymous users can LIST ShowHosts
Status: OPEN
Created: 2026-04-10T11:35:00Z
Scope: api/schedule/views/show.py
Next step: Add authentication required to ShowHostViewSet
Notes: |
  SECURITY ISSUE: Anonymous GET /api/v2/show-hosts returns 200 OK.

  Attack scenario:
  - Unauthenticated attacker lists all show-host assignments
  - Information disclosure of station personnel

  Red team test: test_list_without_auth fails - returns 200 instead of 403

## [CRITICAL] bug T408 — ShowHosts BOLA: no owner filtering
Status: OPEN
Created: 2026-04-10T11:35:00Z
Scope: api/schedule/views/show.py
Next step: Add owner filtering to ShowHostViewSet.get_queryset
Notes: |
  CRITICAL BOLA: ShowHosts list returns ALL assignments regardless of owner.

  Attack scenario:
  - User A can see User B's show assignments
  - User enumeration via user filter
  - Complete information disclosure

  Red team test: test_list_shows_only_own_hosts fails - shows other users' data

## [HIGH] bug T402 — ShowInstances description XSS vulnerability
Status: OPEN
Created: 2026-04-10T11:30:00Z
Scope: api/schedule/serializers/show.py
Next step: Add HTML escaping or use JSON serializer for description
Notes: |
  CRITICAL SECURITY ISSUE: XSS payloads stored unescaped in description.

  Attack scenario:
  - Attacker stores <script>alert('XSS')</script> in description
  - When another user views the show instance, script executes
  - Session hijacking, credential theft possible

  Red team test: test_description_xss fails - payload stored as-is
  Payloads tested: <script>, <img onerror>, javascript: URLs

## [LOW] bug T400 — ShowInstances 404 leaks query keyword
Status: OPEN
Created: 2026-04-10T11:28:00Z
Scope: api/schedule/views/show.py
Next step: Customize 404 error message in ShowInstanceViewSet
Notes: |
  SECURITY ISSUE: 404 response contains "matches the given query".

  Attack scenario:
  - Attacker learns this is a Django ORM-based API
  - Minor information disclosure aids reconnaissance

  Red team test: test_404_leakage fails - "query" in error message
  Current message: "No ShowInstance matches the given query."

## [MEDIUM] bug T396 — ShowDays last_show_on removable via PATCH
Status: OPEN
Created: 2026-04-10T11:27:00Z
Scope: api/schedule/serializers/show.py
Next step: Add validation to prevent null last_show_on if required
Notes: |
  SECURITY ISSUE: PATCH with null last_show_on removes end date.

  Attack scenario:
  - User removes end date on scheduled show
  - Creates infinite repeating show
  - May cause resource exhaustion in scheduler

  Red team test: test_remove_last_show_on_via_patch fails - null accepted

## [MEDIUM] bug T395 — ShowDays accepts negative duration via UPDATE
Status: OPEN
Created: 2026-04-10T11:25:00Z
Scope: api/schedule/serializers/show.py
Next step: Add duration validation in ShowDaysSerializer
Notes: |
  SECURITY ISSUE: PATCH with negative duration is accepted.

  Attack scenario:
  - User sets negative duration via API
  - May cause scheduling logic errors
  - Database stores invalid time value

  Red team test: test_update_to_negative_duration fails - negative duration stored

## [MEDIUM] bug T392 — ShowDays repeat_next_on mutable by user
Status: OPEN
Created: 2026-04-10T11:20:00Z
Scope: api/schedule/serializers/show.py
Next step: Add repeat_next_on to read_only_fields in ShowDaysSerializer
Notes: |
  SECURITY ISSUE: User can manipulate repeat_next_on field during CREATE.

  Attack scenario:
  - User sets arbitrary repeat_next_on date
  - Bypasses internal calculation logic
  - May cause scheduling conflicts or infinite loops

  Red team test: test_repeat_next_on_manipulation fails - field accepted


## [CRITICAL] fix T420 — Playlist ViewSet missing owner-based queryset filtering (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T12:00:00Z
Scope: api/schedule/views/playlist.py
Next step: Add get_queryset() filtering by owner to PlaylistViewSet
Notes: |
  CRITICAL BOLA VULNERABILITY: PlaylistViewSet lacks owner-based filtering.
  
  Current behavior (BROKEN):
  - PlaylistViewSet.queryset = Playlist.objects.all() - returns ALL playlists
  - Any authenticated user with 'delete_playlist' permission can delete ANY playlist
  - Any authenticated user with 'change_playlist' permission can modify ANY playlist
  - Any authenticated user with 'view_playlist' permission can view ANY playlist
  
  Confirmed by existing tests in test_playlist_permissions.py:
  - test_user_can_view_other_users_playlists (lines 106-117)
  - test_user_can_update_other_users_playlists (lines 119-134)  
  - test_user_can_delete_other_users_playlists (lines 136-147)
  
  These tests DOCUMENT the vulnerability but don't prevent it.
  
  Expected behavior:
  - Regular users should only see/modify/delete their own playlists (owner=request.user)
  - Admins can see/modify/delete all playlists
  
  Fix needed:
  - Override get_queryset() in PlaylistViewSet
  - Filter by owner for non-admin users
  - Use existing get_own_obj() pattern from api/permissions.py
  
  Red team tests confirming bug: test_playlist_redteam_t226.py


## [CRITICAL] fix T421 — PlaylistContentViewSet 500 error on invalid playlist filter
Status: NOT_STARTED
Created: 2026-04-10T12:10:00Z
Scope: api/schedule/views/playlist.py:37
Next step: Add input validation for playlist_id parameter in get_queryset
Notes: |
  CRITICAL: Unhandled exception causes 500 Internal Server Error.
  
  Current behavior (BROKEN):
  - GET /api/v2/playlist-contents?playlist=invalid' returns 500
  - GET /api/v2/playlist-contents?playlist={"$ne":null} returns 500
  - Django ValueError not caught: "Field 'id' expected a number but got '...'"
  
  Expected behavior:
  - Invalid playlist parameter should return 400 Bad Request
  - Or return 404 Not Found
  - Never expose 500 errors to client
  
  Root cause:
  - get_queryset() directly passes playlist_id to filter() without validation
  - No try/except around queryset.filter(playlist_id=playlist_id)
  
  Fix needed:
  - Validate playlist_id is numeric before filtering
  - Or catch ValueError and return 400/404
  - Add tests for invalid input handling
  
  Red team tests: test_playlistcontent_list_redteam_t228.py


## [HIGH] fix T422 — IntegrityError on null trackoffset in PlaylistContent
Status: NOT_STARTED
Created: 2026-04-10T12:15:00Z
Scope: api/schedule/models/playlist.py
Next step: Add default value or null=True for trackoffset field
Notes: |
  IntegrityError: null value in column "trackoffset" violates not-null constraint.
  
  Current behavior (BROKEN):
  - POST without offset field causes 500 IntegrityError
  - Database requires trackoffset but model allows null
  
  Expected:
  - Should have default value (0) or proper validation before save
  
  Found by: test_create_wrong_kind_for_file, test_create_null_in_required_fields

## [HIGH] fix T423 — No validation of negative position values
Status: NOT_STARTED
Created: 2026-04-10T12:15:00Z
Scope: api/schedule/serializers/playlist.py
Next step: Add MinValueValidator(0) to position field
Notes: |
  Current behavior (BROKEN):
  - Negative position values accepted without validation
  - Position -1 stored in database
  
  Expected:
  - Should reject negative positions with 400 error

## [HIGH] fix T424 — No rate limiting on content creation
Status: NOT_STARTED
Created: 2026-04-10T12:15:00Z
Scope: api/schedule/views/playlist.py
Next step: Add DRF throttling or custom rate limiting
Notes: |
  Current behavior (BROKEN):
  - Can create 20+ contents instantly without limits
  - No protection against playlist flooding
  
  Expected:
  - Rate limiting per user/IP after N requests
  - Return 429 Too Many Requests


## [CRITICAL] fix T425 — SmartBlock ViewSets missing owner-based queryset filtering (BOLA)
Status: NOT_STARTED
Created: 2026-04-10T12:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add get_queryset() filtering by owner to all SmartBlock ViewSets
Notes: |
  CRITICAL BOLA VULNERABILITY: All SmartBlock ViewSets lack owner-based filtering.
  
  Current behavior (BROKEN):
  - SmartBlockViewSet.queryset = SmartBlock.objects.all() - returns ALL blocks
  - SmartBlockContentViewSet.queryset = SmartBlockContent.objects.all()
  - SmartBlockCriteriaViewSet.queryset = SmartBlockCriteria.objects.all()
  
  Any authenticated user with 'view_smartblock' permission can:
  - List all smart blocks (including other users' private blocks)
  - Access any block by ID
  - Access any content/criteria
  
  Same pattern as T420 (Playlists BOLA).
  
  Red team tests confirming bug: test_smartblock_redteam_t234.py

## [HIGH] fix T426 — SmartBlock CREATE accepts custom id (mass assignment)
Status: NOT_STARTED
Created: 2026-04-10T12:35:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Remove 'id' from writable fields in SmartBlockSerializer
Notes: |
  BOPLA VULNERABILITY: SmartBlockSerializer uses fields = "__all__" which allows
  setting custom id during CREATE.
  
  Attack: POST /api/v2/smart-blocks {"id": 99999, "name": "Test"}
  Result: Block created with attacker-controlled ID, potentially overwriting existing
  records or creating collisions.
  
  Red team test: test_bopla_mass_assignment_id in test_smartblock_create_redteam_t235.py

## [HIGH] fix T427 — SmartBlock CREATE accepts created_at manipulation (mass assignment)
Status: NOT_STARTED
Created: 2026-04-10T12:35:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Remove 'created_at' from writable fields in SmartBlockSerializer
Notes: |
  BOPLA VULNERABILITY: SmartBlockSerializer uses fields = "__all__" which allows
  setting created_at timestamp during CREATE.
  
  Attack: POST /api/v2/smart-blocks {"name": "Test", "created_at": "2020-01-01T00:00:00Z"}
  Result: Block appears to be created in the past, potentially bypassing time-based
  business logic or audit trails.
  
  Red team test: test_bopla_mass_assignment_created_at in test_smartblock_create_redteam_t235.py

## [CRITICAL] fix T428 — SmartBlock CREATE accepts owner manipulation (BOLA vector)
Status: NOT_STARTED
Created: 2026-04-10T12:40:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Remove 'owner' from writable fields in SmartBlockSerializer
Notes: |
  CRITICAL BOPLA/BOLA VULNERABILITY: Attacker can create SmartBlock owned by another user.
  
  Attack: POST /api/v2/smart-blocks {"name": "Malicious", "owner": victim_id}
  Result: Block appears to be owned by victim, potentially hiding malicious content
  or polluting victim's library. Combined with BOLA in LIST, victim sees attacker's block.
  
  Red team test: test_bopla_mass_assignment_owner in test_smartblock_create_redteam_t235.py

## [HIGH] fix T431 — SmartBlock CREATE accepts updated_at manipulation
Status: NOT_STARTED
Created: 2026-04-10T12:40:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Remove 'updated_at' from writable fields in SmartBlockSerializer
Notes: |
  BOPLA VULNERABILITY: Attacker can set arbitrary updated_at timestamp.
  
  Attack: POST /api/v2/smart-blocks {"name": "Test", "updated_at": "2030-12-31T23:59:59Z"}
  Result: Block appears to be updated in future, breaking sorting and audit logic.
  
  Red team test: test_bopla_mass_assignment_updated_at in test_smartblock_create_redteam_t235.py

## [MEDIUM] fix T432 — SmartBlock CREATE accepts arbitrary length values
Status: NOT_STARTED
Created: 2026-04-10T12:40:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Add validation for length field (reasonable min/max)
Notes: |
  BOPLA VULNERABILITY: Attacker can set arbitrary duration values.
  
  Attack: POST /api/v2/smart-blocks {"name": "Test", "length": "PT999999H"}
  Result: Block with impossible duration, may cause UI issues or scheduling errors.
  
  Red team test: test_bopla_mass_assignment_length in test_smartblock_create_redteam_t235.py

## [LOW] fix T433 — No unique constraint on SmartBlock name (race condition possible)
Status: NOT_STARTED
Created: 2026-04-10T12:40:00Z
Scope: api/schedule/models/smart_block.py
Next step: Add unique_together constraint on (name, owner) if business requires
Notes: |
  RACE CONDITION: Multiple blocks with same name can be created concurrently.
  
  Current behavior allows duplicate names which may confuse users.
  Not a security issue but potential data quality concern.
  
  Red team test: test_create_race_condition_duplicate_names in test_smartblock_create_redteam_t235.py

## [CRITICAL] fix T434 — BOLA: Any user can PATCH other user's SmartBlock
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add object-level permission check in SmartBlockViewSet.update
Notes: |
  CRITICAL BOLA VULNERABILITY: No owner verification on PATCH.
  
  Attack: PATCH /api/v2/smart-blocks/{victim_block_id} {"name": "Hacked"}
  Result: Attacker can modify any block by ID, regardless of ownership.
  
  Red team test: test_bola_patch_other_users_block in test_smartblock_update_redteam_t236.py

## [CRITICAL] fix T435 — BOLA: Any user can PUT other user's SmartBlock
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add object-level permission check in SmartBlockViewSet.update
Notes: |
  CRITICAL BOLA VULNERABILITY: No owner verification on PUT.
  
  Attack: PUT /api/v2/smart-blocks/{victim_block_id} {"name": "Hacked", "kind": "static"}
  Result: Attacker can fully replace any block by ID, regardless of ownership.
  
  Red team test: test_bola_put_other_users_block in test_smartblock_update_redteam_t236.py


## [CRITICAL] fix T438 — BOPLA/BOLA: Can change owner via PATCH (block hijacking)
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Make 'owner' read-only in SmartBlockSerializer
Notes: |
  CRITICAL: Attacker can transfer ownership of any block to themselves.
  
  Attack: PATCH /api/v2/smart-blocks/{id} {"owner": attacker_id}
  Result: Block ownership transferred, victim loses access, attacker gains control.
  
  Red team test: test_bopla_patch_change_owner in test_smartblock_update_redteam_t236.py

## [HIGH] fix T439 — BOPLA: Can backdate created_at via PATCH
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Make 'created_at' read-only in SmartBlockSerializer
Notes: |
  BOPLA: Audit trail can be manipulated by changing creation timestamp.
  
  Attack: PATCH /api/v2/smart-blocks/{id} {"created_at": "2010-01-01T00:00:00Z"}
  Result: Block appears to be created years ago, bypassing time-based filters.
  
  Red team test: test_bopla_patch_backdate_created_at in test_smartblock_update_redteam_t236.py

## [MEDIUM] fix T440 — BOPLA: Can set future updated_at via PATCH
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Make 'updated_at' read-only or validate against current time
Notes: |
  BOPLA: Update timestamp can be set to future date.
  
  Attack: PATCH /api/v2/smart-blocks/{id} {"updated_at": "2035-12-31T23:59:59Z"}
  Result: Block appears to be updated in the future, breaking sort order.
  
  Red team test: test_bopla_patch_future_updated_at in test_smartblock_update_redteam_t236.py

## [MEDIUM] fix T441 — BOPLA: Invalid kind values accepted via PATCH
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Add strict validation for kind field choices
Notes: |
  BOPLA: Invalid/null kind values may be accepted, causing data inconsistency.
  
  Attack: PATCH /api/v2/smart-blocks/{id} {"kind": null} or {"kind": "invalid"}
  Result: Block kind may be set to invalid value, breaking business logic.
  
  Red team test: test_bopla_patch_invalid_kind_values in test_smartblock_update_redteam_t236.py

## [HIGH] fix T443 — PUT accepts null for required fields (validation bypass)
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Scope: api/schedule/serializers/smart_block.py
Next step: Add validation to reject null for required fields (name, kind)
Notes: |
  VALIDATION BYPASS: PUT /api/v2/smart-blocks/{id} accepts null values for required fields.
  
  Expected: 400 Bad Request when trying to set name=null or kind=null
  Actual: Returns 200 OK and accepts the null values
  
  Test: test_validation_put_null_required_fields (currently fails)
  Test: test_validation_put_null_required_fields_xfail (documents bug)
  
  Red team test: test_validation_put_null_required_fields in test_smartblock_update_redteam_t236.py

## [CRITICAL] fix T444 — BOLA: Any user can DELETE other user's SmartBlock
Status: NOT_STARTED
Created: 2026-04-10T16:10:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add object-level permission check in SmartBlockViewSet.destroy
Notes: |
  CRITICAL BOLA VULNERABILITY: No owner verification on DELETE.
  
  Attack: DELETE /api/v2/smart-blocks/{victim_block_id}
  Result: Attacker can delete any block by ID, regardless of ownership.
  
  Red team test: test_bola_delete_other_users_block in test_smartblock_delete_redteam_t237.py

## [CRITICAL] fix T445 — BOLA: Cascade delete allows destroying other user's content
Status: NOT_STARTED
Created: 2026-04-10T16:10:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add ownership check before allowing cascade delete
Notes: |
  CRITICAL BOLA: Deleting a block cascades to SmartBlockContent/SmartBlockCriteria.
  
  If attacker can delete victim's block (T444), they also delete all associated
  content and criteria, amplifying the damage.
  
  Red team test: test_bola_cascade_delete_other_user_content in test_smartblock_delete_redteam_t237.py

## [MEDIUM] fix T446 — Information disclosure: 404 vs 403 leaks block existence
Status: NOT_STARTED
Created: 2026-04-10T16:10:00Z
Scope: api/schedule/views/smart_block.py
Next step: Return 403 for both existing and non-existing blocks when unauthorized
Notes: |
  SIDE CHANNEL: Different error codes leak whether block exists.
  
  Current: Non-existing returns 404, existing (but not owned) returns 403
  Secure: Both should return 403 to not leak existence
  
  Attack: Attacker can enumerate valid block IDs by observing 404 vs 403
  
  Red team test: test_bola_delete_leaks_block_existence in test_smartblock_delete_redteam_t237.py

## [CRITICAL] fix T447 — HTTP Method Override bypasses DELETE protection
Status: NOT_STARTED
Created: 2026-04-10T16:10:00Z
Scope: api/schedule/views/smart_block.py
Next step: Ignore X-HTTP-Method-Override or validate against actual method
Notes: |
  CRITICAL: X-HTTP-Method-Override header causes unintended deletion.
  
  Attack: DELETE /api/v2/smart-blocks/{id} with X-HTTP-Method-Override: GET
  Result: Block is deleted even though override suggests GET!
  
  This may bypass CSRF protections or method-based access controls.
  
  Red team test: test_http_method_override_on_delete in test_smartblock_delete_redteam_t237.py

## [CRITICAL] fix T448 — BOLA: LIST endpoint shows all users' blocks without filtering
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add owner filtering to SmartBlockViewSet.get_queryset()
Notes: |
  CRITICAL BOLA: LIST /api/v2/smart-blocks returns ALL blocks from ALL users.
  
  Attack: Any authenticated user lists blocks
  Result: Sees private blocks from all other users
  
  Same root cause as T425 (missing owner filtering).
  
  Red team test: test_bola_list_shows_all_users_blocks in test_smartblock_permissions_redteam_t238.py

## [CRITICAL] fix T449 — BOLA: RETRIEVE allows access to any block by ID
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add object-level permission check in retrieve
Notes: |
  CRITICAL BOLA: GET /api/v2/smart-blocks/{id} works for any block ID.
  
  Attack: Attacker tries to GET victim's private block by ID
  Result: Receives full block details including name, description, contents
  
  No ownership verification on retrieve.
  
  Red team test: test_bola_retrieve_other_users_private_block in test_smartblock_permissions_redteam_t238.py

## [HIGH] fix T450 — BOLA: Block ID enumeration possible
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add rate limiting or require owner filter
Notes: |
  BOLA + IDOR: Sequential IDs allow enumeration of all blocks.
  
  Attack: Attacker iterates through IDs 1..N, calling GET for each
  Result: Can discover all blocks in the system
  
  Combined with T449, allows complete data extraction.
  
  Red team test: test_bola_block_id_enumeration in test_smartblock_permissions_redteam_t238.py

## [MEDIUM] fix T451 — BFLA: Bulk delete endpoint may exist
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Verify /bulk-delete endpoint doesn't exist or is protected
Notes: |
  BFLA: Testing for potential admin-only bulk operations.
  
  Current status: Endpoint returns 404 (doesn't exist) - ACCEPTABLE
  If endpoint exists and is accessible - CRITICAL vulnerability.
  
  Red team test: test_bfla_admin_bulk_delete_accessible in test_smartblock_permissions_redteam_t238.py

## [MEDIUM] fix T453 — BFLA: Import endpoint may exist
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Verify /import endpoint doesn't exist or is admin-only
Notes: |
  BFLA: Testing for potential admin-only import operations.
  
  Current status: Endpoint returns 404 (doesn't exist) - ACCEPTABLE
  
  Red team test: test_bfla_admin_import_accessible in test_smartblock_permissions_redteam_t238.py

## [MEDIUM] fix T454 — Privilege escalation: HOST role can perform admin actions
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Verify HOST users cannot create blocks for other users
Notes: |
  PRIVILEGE ESCALATION: HOST role trying to perform admin-like actions.
  
  Test: Creating blocks with owner set to other user
  Risk: If successful, HOST can impersonate/spoof other users' content
  
  Red team test: test_privesc_host_to_admin_actions in test_smartblock_permissions_redteam_t238.py

## [MEDIUM] fix T455 — Privilege escalation: DJ role bypass
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Verify DJ role has appropriate restrictions
Notes: |
  PRIVILEGE ESCALATION: DJ users should have read-only or limited access.
  
  DJ role should not be able to create/modify blocks (business logic).
  Current behavior needs verification.
  
  Red team test: test_privesc_dj_role_bypass in test_smartblock_permissions_redteam_t238.py

## [MEDIUM] fix T456 — Privilege escalation: Guest role has unexpected access
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/schedule/views/smart_block.py
Next step: Restrict Guest role to read-only on public content only
Notes: |
  PRIVILEGE ESCALATION: Guest users should have minimal access.
  
  Guest role should only view public content, no modifications.
  Current access level needs audit.
  
  Red team test: test_privesc_guest_role_access in test_smartblock_permissions_redteam_t238.py

## [HIGH] fix T459 — Auth bypass: Case-insensitive authorization header accepted
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/permissions.py or middleware
Next step: Reject lowercase 'authorization' header
Notes: |
  AUTH BYPASS: HTTP header 'authorization' (lowercase) bypasses auth checks.
  
  Standard: 'Authorization' (capital A)
  Bug: 'authorization' (lowercase) accepted without proper validation
  
  This may allow bypass of API key checks.
  
  Red team test: test_auth_bypass_case_insensitive_headers in test_smartblock_permissions_redteam_t238.py

## [CRITICAL] fix T460 — Auth bypass: Empty/malformed tokens accepted
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/permissions.py
Next step: Reject empty or malformed Authorization headers
Notes: |
  CRITICAL AUTH BYPASS: Empty Authorization header grants access.
  
  Attack: curl -H "Authorization:" /api/v2/smart-blocks
  Result: Returns 200 with data instead of 403
  
  Same for: "Bearer", "Bearer ", "null", "undefined"
  
  Red team test: test_auth_bypass_empty_token in test_smartblock_permissions_redteam_t238.py

## [HIGH] fix T458 — Privilege escalation: Can change own role to ADMIN
Status: NOT_STARTED
Created: 2026-04-10T16:20:00Z
Scope: api/core/views/user.py or similar
Next step: Make 'role' field read-only for self-updates
Notes: |
  PRIVILEGE ESCALATION: User can change their role to ADMIN via PATCH.
  
  Attack: PATCH /api/v2/users/me {"role": "admin"}
  Result: User gains admin privileges
  
  Or endpoint /api/v2/users/me may not exist (returns 404) - verify.
  
  Red team test: test_perm_mass_assignment_role_escalation in test_smartblock_permissions_redteam_t238.py


## [CRITICAL] fix T461 — BOLA: LIST shows all users' SmartBlockContents
Status: NOT_STARTED
Created: 2026-04-10T16:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add owner filtering via block__owner to SmartBlockContentViewSet
Notes: |
  CRITICAL BOLA: LIST /api/v2/smart-block-contents returns ALL content from ALL users.
  
  Attack: Any authenticated user lists contents
  Result: Sees all content items including those in other users' private blocks
  
  Red team test: test_bola_list_shows_all_users_content in test_smartblockcontent_list_redteam_t239.py

## [CRITICAL] fix T462 — BOLA: Filter by block ID bypasses ownership
Status: NOT_STARTED
Created: 2026-04-10T16:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Verify block ownership before applying block filter
Notes: |
  CRITICAL BOLA: ?block={id} filter works for any block ID without ownership check.
  
  Attack: GET /api/v2/smart-block-contents?block={victim_block_id}
  Result: Returns all contents from victim's block
  
  Red team test: test_bola_filter_by_other_users_block in test_smartblockcontent_list_redteam_t239.py

## [MEDIUM] fix T464 — SQL injection in block filter parameter
Status: NOT_STARTED
Created: 2026-04-10T16:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Use parameterized queries or ORM properly
Notes: |
  SQLi: Malicious payloads in block filter may execute SQL.
  
  Attack: GET /api/v2/smart-block-contents?block=1' OR '1'='1
  Risk: Potential data extraction or modification
  
  Red team test: test_filter_sql_injection_block_param in test_smartblockcontent_list_redteam_t239.py

## [HIGH] fix T472 — 500 error on non-numeric block_id filter parameter
Status: NOT_STARTED
Created: 2026-04-10T16:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add validation for block_id parameter before filtering
Notes: |
  DOS/INFO LEAK: Non-numeric block_id causes 500 Internal Server Error.
  
  Attack: GET /api/v2/smart-block-contents?block=abc
  Result: 500 error with stack trace instead of 400 Bad Request
  
  This reveals implementation details and can be used for DoS.
  
  Red team test: test_filter_non_numeric_block_id in test_smartblockcontent_list_redteam_t239.py

## [HIGH] fix T473 — 500 error on unicode block_id filter parameter
Status: NOT_STARTED
Created: 2026-04-10T16:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Add validation for block_id parameter encoding
Notes: |
  DOS/INFO LEAK: Unicode block_id causes 500 Internal Server Error.
  
  Attack: GET /api/v2/smart-block-contents?block=日本語
  Result: 500 error instead of 400 Bad Request
  
  Red team test: test_filter_unicode_block_id in test_smartblockcontent_list_redteam_t239.py

## [HIGH] fix T474 — 500 error on special query params (undefined, null, None)
Status: NOT_STARTED
Created: 2026-04-10T16:30:00Z
Scope: api/schedule/views/smart_block.py
Next step: Handle special string values gracefully
Notes: |
  DOS/INFO LEAK: Special JavaScript-like values cause 500 errors.
  
  Attack: GET /api/v2/smart-block-contents?block=undefined
  Result: 500 error - Django tries to convert "undefined" to number
  
  These values are common in JavaScript/frontend contexts.
  
  Red team test: test_fuzzing_query_params in test_smartblockcontent_list_redteam_t239.py

## [HIGH] fix T556 — BOLA: DELETE returns 404 instead of 403 for other user's stream
Status: NOT_STARTED
Created: 2026-04-10T13:33:00Z
Last worked: 2026-04-10T13:33:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Return 403 for unauthorized access instead of 404 to prevent info leak
Notes: |
  DELETE of other user's stream returns 404 (not found) instead of 403 (forbidden).
  This leaks information about stream existence (different error for existing vs non-existing).
  Ref: test_webstream_delete_redteam_t248.py::test_bola_delete_other_users_stream_status

## [CRITICAL] fix T557 — BOLA: Batch delete affects multiple streams
Status: NOT_STARTED
Created: 2026-04-10T13:33:00Z
Last worked: 2026-04-10T13:33:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add proper query filtering to ensure single-record scope
Notes: |
  DELETE request may affect multiple streams instead of single target.
  Indicates lack of proper object-level authorization scope.
  Ref: test_webstream_delete_redteam_t248.py::test_bola_batch_delete_scope

## [MEDIUM] fix T558 — Error message leaks webstream existence
Status: NOT_STARTED
Created: 2026-04-10T13:33:00Z
Last worked: 2026-04-10T13:33:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Unify error responses for existing/non-existing on unauthorized
Notes: |
  Different error messages for existing (permission denied) vs non-existing streams
  allow attackers to enumerate which webstream IDs exist.
  Ref: test_webstream_delete_redteam_t248.py::test_error_message_leaks_existence

## [MEDIUM] fix T559 — Race condition in concurrent webstream delete
Status: NOT_STARTED
Created: 2026-04-10T13:33:00Z
Last worked: 2026-04-10T13:33:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add row-level locking or optimistic concurrency control
Notes: |
  Multiple concurrent DELETE requests for same stream cause inconsistent results.
  Race condition can lead to data corruption or unexpected behavior.
  Ref: test_webstream_delete_redteam_t248.py::test_race_condition_concurrent_delete

## [LOW] fix T560 — Invalid auth token returns inconsistent status
Status: NOT_STARTED
Created: 2026-04-10T13:33:00Z
Last worked: 2026-04-10T13:33:00Z
File: `app/api/api/permissions.py:85-95`
Next step: Standardize auth error responses to always return 401/403
Notes: |
  DELETE with invalid token returns wrong status code instead of consistent 403.
  Inconsistent error handling may reveal implementation details.
  Ref: test_webstream_delete_redteam_t248.py::test_delete_with_invalid_token

## [MEDIUM] fix T561 — HTTP method override bypasses delete protection
Status: NOT_STARTED
Created: 2026-04-10T13:33:00Z
Last worked: 2026-04-10T13:33:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Block or properly handle X-HTTP-Method-Override headers
Notes: |
  HTTP method override (X-HTTP-Method-Override: DELETE) may bypass delete restrictions.
  Method override protection not properly enforced.
  Ref: test_webstream_delete_redteam_t248.py::test_http_method_override_delete

## [CRITICAL] fix T562 — BOLA: Any user can modify other user's webstream
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add ownership check in update/patch operations
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can UPDATE victim's
  webstream by knowing the ID. No ownership validation.
  Ref: test_webstream_permissions_redteam_t249.py::test_bola_modify_other_users_webstream

## [CRITICAL] fix T563 — BOLA: Any user can delete other user's webstream
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Add ownership check in destroy operation
Notes: |
  Attacker can DELETE victim's webstream by knowing the ID.
  Critical data loss vulnerability.
  Ref: test_webstream_permissions_redteam_t249.py::test_bola_delete_other_users_webstream

## [HIGH] fix T564 — BOLA: LIST endpoint returns all users' webstreams
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/webstream.py:14-25`
Next step: Filter queryset to only current user's webstreams
Notes: |
  GET /api/v2/webstreams returns webstreams from all users instead of only current user.
  Information disclosure vulnerability allowing ID enumeration for further BOLA attacks.
  Ref: test_webstream_permissions_redteam_t249.py::test_bola_batch_access_all_streams

## [HIGH] fix T567 — BOPLA: Can change owner to another user during UPDATE
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/serializers/webstream.py:12-38`
Next step: Remove owner from writable fields or add validation
Notes: |
  PATCH request with owner field allows changing webstream ownership to another user.
  Mass assignment vulnerability enabling privilege escalation and account hijacking.
  Ref: test_webstream_permissions_redteam_t249.py::test_bopla_mass_assignment_owner_update


## [HIGH] fix T568 — BOLA: Schedule LIST shows all users' entries
Status: NOT_STARTED
Created: 2026-04-10T14:35:00Z
Last worked: 2026-04-10T14:35:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Filter queryset to only current user's schedule entries
Notes: |
  API1:2023 Broken Object Level Authorization. LIST endpoint returns schedule
  entries from all users without ownership filtering.
  Ref: test_schedule_list_redteam_t250.py::test_bola_list_shows_all_users_schedule

## [CRITICAL] fix T569 — BOLA: Can access other user's schedule by ID
Status: NOT_STARTED
Created: 2026-04-10T14:35:00Z
Last worked: 2026-04-10T14:35:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add ownership check in retrieve operation
Notes: |
  Attacker can retrieve victim's schedule entry by knowing the ID.
  No object-level permission validation on individual resource access.
  Ref: test_schedule_list_redteam_t250.py::test_bola_access_other_users_schedule_by_id

## [MEDIUM] fix T573 — Info Leak: Error message reveals schedule existence
Status: NOT_STARTED
Created: 2026-04-10T14:35:00Z
Last worked: 2026-04-10T14:35:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Unify error responses for existing/non-existing resources
Notes: |
  Different error codes for existing (permission denied) vs non-existing
  schedule entries allow ID enumeration attacks.
  Ref: test_schedule_list_redteam_t250.py::test_error_message_leaks_existence

## [CRITICAL] fix T574 — BOLA: Filter combination bypasses ownership
Status: NOT_STARTED
Created: 2026-04-10T14:35:00Z
Last worked: 2026-04-10T14:35:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Apply ownership filter before any other filters
Notes: |
  Combining multiple filter parameters (instance, position, broadcasted)
  may bypass ownership checks and reveal other users' schedule data.
  Ref: test_schedule_list_redteam_t250.py::test_filter_combination_bypass

## [CRITICAL] fix T575 — Auth: Invalid token returns 200 instead of 403
Status: NOT_STARTED
Created: 2026-04-10T14:35:00Z
Last worked: 2026-04-10T14:35:00Z
File: `app/api/api/permissions.py:85-95`
Next step: Reject requests with invalid/malformed authentication tokens
Notes: |
  API requests with invalid Bearer token return 200 OK instead of 403.
  Authentication bypass allowing unauthorized access to protected resources.
  Ref: test_schedule_list_redteam_t250.py::test_list_with_invalid_token


## [CRITICAL] fix T576 — BOLA: Can create schedule for other user's show
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate instance ownership before creating schedule
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can create schedule entries
  in victim's show instance by knowing the instance ID. No ownership validation.
  Ref: test_schedule_create_redteam_t251.py::test_bola_create_schedule_for_other_user_show

## [CRITICAL] fix T577 — BOLA: Can create schedule using other user's file
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate file ownership during schedule creation
Notes: |
  Attacker can create schedule using victim's file without permission.
  File ownership not verified during CREATE operation.
  Ref: test_schedule_create_redteam_t251.py::test_bola_create_schedule_with_other_user_file

## [CRITICAL] fix T578 — BOLA: Can create schedule using other user's stream
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate webstream ownership during schedule creation
Notes: |
  Attacker can create schedule using victim's webstream without permission.
  Stream ownership not verified during CREATE operation.
  Ref: test_schedule_create_redteam_t251.py::test_bola_create_schedule_with_other_user_stream

## [HIGH] fix T581 — Business Logic: No schedule overlap validation
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add overlap validation in create/save operations
Notes: |
  API allows creating overlapping schedule entries in same show instance.
  No validation prevents scheduling conflicts.
  Ref: test_schedule_create_redteam_t251.py::test_business_logic_schedule_overlap

## [HIGH] fix T582 — Business Logic: No show time boundary validation
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate schedule time within show instance boundaries
Notes: |
  API allows creating schedule entries outside show instance time boundaries.
  Schedule entries can be created for times when show is not active.
  Ref: test_schedule_create_redteam_t251.py::test_business_logic_outside_show_time

## [HIGH] fix T583 — SSRF: Schedule created with internal stream URL
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Block stream URLs pointing to internal/metadata endpoints
Notes: |
  Can create schedule using webstream with internal/metadata URLs.
  May lead to SSRF when schedule is played and stream URL is fetched.
  Ref: test_schedule_create_redteam_t251.py::test_ssrf_create_schedule_with_internal_stream

## [CRITICAL] fix T584 — Auth: CREATE with invalid token returns 200
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/permissions.py:85-95`
Next step: Reject requests with invalid/malformed authentication tokens
Notes: |
  Same as T575. POST with invalid Bearer token returns 200 OK instead of 403.
  Authentication bypass allowing unauthorized schedule creation.
  Ref: test_schedule_create_redteam_t251.py::test_create_with_invalid_token

## [MEDIUM] fix T586 — Race condition: Concurrent CREATE same slot
Status: NOT_STARTED
Created: 2026-04-10T14:45:00Z
Last worked: 2026-04-10T14:45:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add unique constraints or row-level locking
Notes: |
  Multiple concurrent CREATE requests can create multiple schedules for same slot.
  Race condition in create operation leads to data inconsistency.
  Ref: test_schedule_create_redteam_t251.py::test_race_condition_concurrent_create


## [CRITICAL] fix T587 — BOLA: Can retrieve other user's schedule
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add ownership check in retrieve operation
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can retrieve victim's
  schedule entry by knowing the ID. No object-level permission validation.
  Ref: test_schedule_retrieve_redteam_t253.py::test_bola_retrieve_other_users_schedule

## [CRITICAL] fix T589 — Auth: RETRIEVE with invalid token returns 200
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/permissions.py:85-95`
Next step: Reject requests with invalid/malformed authentication tokens
Notes: |
  Same as T575/T584/T597. GET with invalid Bearer token returns 200 OK.
  Authentication bypass allowing unauthorized access to schedule data.
  Ref: test_schedule_retrieve_redteam_t253.py::test_retrieve_with_invalid_token

## [MEDIUM] fix T591 — Info Leak: Error message reveals schedule existence
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Unify error responses for existing/non-existing resources
Notes: |
  Different error codes for existing (permission denied) vs non-existing
  schedule entries allow ID enumeration attacks.
  Ref: test_schedule_retrieve_redteam_t253.py::test_error_message_leaks_existence_retrieve

## [CRITICAL] fix T592 — BOLA: Can update other user's schedule
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add ownership check in update operation
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can UPDATE victim's
  schedule entry by knowing the ID. No ownership validation.
  Ref: test_schedule_update_redteam_t254.py::test_bola_update_other_users_schedule

## [CRITICAL] fix T593 — BOLA: Can change schedule to other user's file
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate file ownership during schedule update
Notes: |
  Attacker can update schedule to use victim's file without permission.
  File ownership not verified during UPDATE operation.
  Ref: test_schedule_update_redteam_t254.py::test_bola_update_to_other_user_file

## [CRITICAL] fix T594 — BOLA: Can change schedule to other user's stream
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate webstream ownership during schedule update
Notes: |
  Attacker can update schedule to use victim's webstream without permission.
  Stream ownership not verified during UPDATE operation.
  Ref: test_schedule_update_redteam_t254.py::test_bola_update_to_other_user_stream

## [HIGH] fix T595 — Business Logic: Can create overlap via UPDATE
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add overlap validation in update operations
Notes: |
  API allows creating overlapping schedule entries via UPDATE.
  No validation prevents scheduling conflicts during update.
  Ref: test_schedule_update_redteam_t254.py::test_business_logic_overlap_via_update

## [HIGH] fix T596 — SSRF: Can update to internal stream URL
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Block stream URLs pointing to internal/metadata endpoints
Notes: |
  Can update schedule to use webstream with internal/metadata URLs.
  May lead to SSRF when schedule is played and stream URL is fetched.
  Ref: test_schedule_update_redteam_t254.py::test_ssrf_update_to_internal_stream

## [CRITICAL] fix T597 — Auth: UPDATE with invalid token returns 200
Status: NOT_STARTED
Created: 2026-04-10T15:00:00Z
Last worked: 2026-04-10T15:00:00Z
File: `app/api/api/permissions.py:85-95`
Next step: Reject requests with invalid/malformed authentication tokens
Notes: |
  Same as T575/T584/T589. PATCH/PUT with invalid Bearer token returns 200.
  Authentication bypass allowing unauthorized schedule modification.
  Ref: test_schedule_update_redteam_t254.py::test_update_with_invalid_token


## [CRITICAL] fix T598 — BOLA: Can delete other user's schedule
Status: NOT_STARTED
Created: 2026-04-10T16:15:00Z
Last worked: 2026-04-10T16:15:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add ownership check in destroy operation
Notes: |
  API1:2023 Broken Object Level Authorization. Attacker can DELETE victim's
  schedule entry by knowing the ID. No object-level permission validation.
  Ref: test_schedule_delete_redteam_t255.py::test_bola_delete_other_users_schedule

## [HIGH] fix T599 — BOLA: DELETE returns wrong status for other's schedule
Status: NOT_STARTED
Created: 2026-04-10T16:15:00Z
Last worked: 2026-04-10T16:15:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Return 403 for unauthorized delete instead of 404/204
Notes: |
  DELETE of other user's schedule returns wrong status (404 or 204 instead of 403).
  404 leaks schedule existence, 204 allows deletion - both are vulnerabilities.
  Ref: test_schedule_delete_redteam_t255.py::test_bola_delete_other_users_schedule_status

## [CRITICAL] fix T600 — Auth: DELETE with invalid token returns 200
Status: NOT_STARTED
Created: 2026-04-10T16:15:00Z
Last worked: 2026-04-10T16:15:00Z
File: `app/api/api/permissions.py:85-95`
Next step: Reject requests with invalid/malformed authentication tokens
Notes: |
  Same as T575/T584/T589/T597. DELETE with invalid Bearer token returns 200/204.
  Authentication bypass allowing unauthorized schedule deletion.
  Ref: test_schedule_delete_redteam_t255.py::test_delete_with_invalid_token

## [MEDIUM] fix T601 — Mass deletion: No rate limiting on delete
Status: NOT_STARTED
Created: 2026-04-10T16:15:00Z
Last worked: 2026-04-10T16:15:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Implement rate limiting for DELETE operations
Notes: |
  Rapid sequential DELETE requests not rate limited. Can mass-delete schedules.
  DoS vector through schedule deletion flooding.
  Ref: test_schedule_delete_redteam_t255.py::test_mass_deletion_rate_limit

## [MEDIUM] fix T602 — Info Leak: DELETE error reveals schedule existence
Status: NOT_STARTED
Created: 2026-04-10T16:15:00Z
Last worked: 2026-04-10T16:15:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Unify error responses for existing/non-existing on unauthorized
Notes: |
  Different status codes for existing (permission denied) vs non-existing schedules
  allow attackers to enumerate which schedule IDs exist.
  Ref: test_schedule_delete_redteam_t255.py::test_error_message_leaks_existence_delete

## [CRITICAL] fix T602 — Info Leak: DELETE error reveals schedule existence
Status: NOT_STARTED
Created: 2026-04-10T16:15:00Z
Last worked: 2026-04-10T16:15:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Unify error responses for existing/non-existing on unauthorized
Notes: |
  Different status codes for existing (permission denied) vs non-existing schedules
  allow attackers to enumerate which schedule IDs exist.
  Ref: test_schedule_delete_redteam_t255.py::test_error_message_leaks_existence_delete


## [CRITICAL] fix T612 — BOLA: Cross-instance access reveals schedules
Status: NOT_STARTED
Created: 2026-04-10T13:30:00Z
Last worked: 2026-04-10T13:30:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add cross-instance permission checks
Notes: |
  API1:2023 BOLA. User can access schedules across different show instances.
  No validation ensures user can only access schedules for shows they own.
  Ref: test_schedule_permissions_redteam_t256.py::test_cross_instance_access

## [HIGH] fix T613 — Injection: SQLi in overbooked filter parameter
Status: NOT_STARTED
Created: 2026-04-10T13:30:00Z
Last worked: 2026-04-10T13:30:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate and sanitize overbooked parameter
Notes: |
  API8:2023 Injection. Malicious payloads in overbooked filter can cause
  unexpected behavior or potential SQL injection.
  Ref: test_schedule_overbooked_redteam_t257.py::test_overbooked_sql_injection

## [MEDIUM] fix T615 — Filter: overbooked logic bypass
Status: NOT_STARTED
Created: 2026-04-10T13:30:00Z
Last worked: 2026-04-10T13:30:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Fix overbooked filter logic for edge cases
Notes: |
  API6:2023 Unsafe Business Flows. Filter logic can be bypassed when
  show instance has no ends_at or unusual date configurations.
  Ref: test_schedule_overbooked_redteam_t257.py::test_overbooked_logic_bypass

## [CRITICAL] fix T616 — BOLA: overbooked filter reveals other users' schedules
Status: NOT_STARTED
Created: 2026-04-10T13:30:00Z
Last worked: 2026-04-10T13:30:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add user isolation to overbooked filter
Notes: |
  API1:2023 BOLA. overbooked filter returns schedules from all users,
  not just the requesting user's schedules.
  Ref: test_schedule_overbooked_redteam_t257.py::test_overbooked_bola_info_leak



## [CRITICAL] fix T617 — BOLA: Host can modify other host's show schedule
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add show ownership validation in update operations
Notes: |
  API1:2023 BOLA. Host can PATCH schedule entries belonging to other hosts' shows.
  No validation ensures host can only modify schedules for shows they are assigned to.
  Ref: test_schedule_show_host_permissions_redteam_t258.py::test_host_cannot_modify_other_host_show

## [CRITICAL] fix T618 — BOLA: Host can delete other host's show schedule
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Add show ownership validation in delete operations
Notes: |
  API1:2023 BOLA. Host can DELETE schedule entries belonging to other hosts' shows.
  Same root cause as T617 - missing show ownership check.
  Ref: test_schedule_show_host_permissions_redteam_t258.py::test_host_cannot_delete_other_host_show

## [HIGH] fix T619 — BOPLA: Host can change schedule to other show instance
Status: NOT_STARTED
Created: 2026-04-10T14:00:00Z
Last worked: 2026-04-10T14:00:00Z
File: `app/api/api/schedule/views/schedule.py:38-45`
Next step: Validate instance ownership during schedule update
Notes: |
  API3:2023 BOPLA. Host can change schedule's instance_id to another host's show.
  Allows moving schedule between shows without permission validation.
  Ref: test_schedule_show_host_permissions_redteam_t258.py::test_host_cannot_change_to_other_show_instance

## [MEDIUM] fix T620 — No rate limiting on PlayoutHistory LIST endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:30:00Z
Last worked: 2026-04-10T15:30:00Z
File: `app/api/api/history/views/played.py:21-26`
Next step: Add Django Ratelimit or DRF throttling to PlayoutHistoryViewSet
Notes: |
  API4:2023 Unrestricted Resource Consumption. LIST endpoint has no rate limiting.
  Rapid sequential requests (20 requests) all succeed with 200.
  Can lead to DoS via resource exhaustion.
  Ref: test_playout_history_list_redteam_t259.py::test_rapid_sequential_requests

## [MEDIUM] fix T621 — BOPLA: PlayoutHistory CREATE accepts extra/unknown fields
Status: NOT_STARTED
Created: 2026-04-10T15:35:00Z
Last worked: 2026-04-10T15:35:00Z
File: `app/api/api/history/serializers/played.py:13-17`
Next step: Add strict validation or use explicit fields list instead of __all__
Notes: |
  API3:2023 Broken Object Property Level Authorization. CREATE accepts extra fields
  like "is_admin", "role", "password" and silently ignores them instead of rejecting.
  Can mask typos or attempted mass assignment attacks.
  Ref: test_playout_history_create_redteam_t260.py::test_bopla_extra_fields_not_rejected

## [CRITICAL] fix T622 — BOLA: PlayoutHistory CREATE links to other user's instance
Status: NOT_STARTED
Created: 2026-04-10T15:35:00Z
Last worked: 2026-04-10T15:35:00Z
File: `app/api/api/history/serializers/played.py:13-28`
Next step: Add instance ownership validation in serializer or viewset
Notes: |
  API1:2023 Broken Object Level Authorization. CREATE allows specifying any instance_id
  regardless of show ownership. Attacker can link playout to victim's private show.
  No validation that requesting user owns the referenced show instance.
  Ref: test_playout_history_create_redteam_t260.py::test_bola_create_with_other_users_instance

## [MEDIUM] fix T623 — No rate limiting on PlayoutHistory CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:35:00Z
Last worked: 2026-04-10T15:35:00Z
File: `app/api/api/history/views/played.py:21-26`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. CREATE endpoint has no rate limiting.
  Rapid sequential CREATE requests (20 requests) all succeed with 201.
  Can lead to database spam and resource exhaustion.
  Ref: test_playout_history_create_redteam_t260.py::test_create_rapid_fire

## [MEDIUM] fix T624 — BOPLA: PlayoutHistory UPDATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/history/serializers/played.py:13-17`
Next step: Add strict validation on UPDATE/PATCH for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. PUT/PATCH accepts extra fields
  like "is_admin", "role", "invalid_field" and silently ignores them.
  Should reject with 400 for unknown fields to prevent mass assignment attempts.
  Ref: test_playout_history_rud_redteam_t261.py::test_bopla_full_update_with_invalid_field

## [MEDIUM] fix T625 — BOPLA: PlayoutHistory PATCH accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/history/serializers/played.py:13-17`
Next step: Add strict validation on PATCH for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. PATCH silently ignores
  unknown fields like "hacked": True, "role": "superuser" instead of rejecting.
  Can mask attempted mass assignment attacks.
  Ref: test_playout_history_rud_redteam_t261.py::test_bopla_patch_extra_fields_ignored

## [CRITICAL] fix T626 — BOLA: Metadata CREATE for other user's playout
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Last worked: 2026-04-10T15:45:00Z
File: `app/api/api/history/serializers/played.py:31-34`
Next step: Add history ownership validation in metadata serializer
Notes: |
  API1:2023 Broken Object Level Authorization. CREATE metadata allows specifying
  any history_id regardless of ownership. Attacker can add metadata to victim's playout.
  No validation that requesting user owns the referenced playout history.
  Ref: test_playout_history_metadata_redteam_t262.py::test_bola_create_metadata_for_other_users_playout

## [MEDIUM] fix T627 — BOPLA: Metadata CREATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Last worked: 2026-04-10T15:45:00Z
File: `app/api/api/history/serializers/played.py:31-34`
Next step: Add strict validation to reject unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. CREATE accepts extra fields
  like "is_admin", "password" and silently ignores them instead of rejecting.
  Ref: test_playout_history_metadata_redteam_t262.py::test_bopla_create_extra_fields_ignored

## [MEDIUM] fix T628 — BOPLA: Metadata UPDATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Last worked: 2026-04-10T15:45:00Z
File: `app/api/api/history/serializers/played.py:31-34`
Next step: Add strict validation on UPDATE/PATCH for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. PUT/PATCH accepts extra fields
  and silently ignores them. Should reject with 400 for unknown fields.
  Ref: test_playout_history_metadata_redteam_t262.py::test_bopla_update_extra_fields_ignored

## [HIGH] fix T629 — XSS: Metadata key field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Last worked: 2026-04-10T15:45:00Z
File: `app/api/api/history/serializers/played.py:31-34`
Next step: Add HTML sanitization for key field or validate against HTML tags
Notes: |
  XSS vulnerability. Script tags in key field are stored and returned without sanitization.
  Potential reflected/stored XSS if rendered in frontend without escaping.
  Ref: test_playout_history_metadata_redteam_t262.py::test_xss_in_key_field

## [HIGH] fix T630 — XSS: Metadata value field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Last worked: 2026-04-10T15:45:00Z
File: `app/api/api/history/serializers/played.py:31-34`
Next step: Add HTML sanitization for value field or validate against HTML tags
Notes: |
  XSS vulnerability. Script tags and event handlers in value field are stored
  without sanitization. Can lead to stored XSS attacks.
  Ref: test_playout_history_metadata_redteam_t262.py::test_xss_in_value_field

## [MEDIUM] fix T631 — No rate limiting on metadata CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:45:00Z
Last worked: 2026-04-10T15:45:00Z
File: `app/api/api/history/views/played.py:28-33`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. Metadata CREATE has no rate limiting.
  Rapid sequential requests (20) all succeed with 201. Can spam database.
  Ref: test_playout_history_metadata_redteam_t262.py::test_rapid_metadata_creation

## [MEDIUM] fix T632 — BOPLA: Template CREATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/serializers/played.py:37-40`
Next step: Add strict validation to reject unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. Template CREATE accepts
  extra fields like "is_admin", "password", "role" and silently ignores them.
  Should reject with 400 for unknown fields.
  Ref: test_playout_history_template_redteam_t263.py::test_bopla_create_extra_fields_ignored

## [MEDIUM] fix T633 — BOPLA: Template UPDATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/serializers/played.py:37-40`
Next step: Add strict validation on PUT for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. Template PUT accepts
  extra fields like "hacked", "system_field" and silently ignores them.
  Ref: test_playout_history_template_redteam_t263.py::test_bopla_update_extra_fields_ignored

## [MEDIUM] fix T634 — BOPLA: Template PATCH accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/serializers/played.py:37-40`
Next step: Add strict validation on PATCH for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. Template PATCH accepts
  extra fields like "is_system", "internal_flag" and silently ignores them.
  Ref: test_playout_history_template_redteam_t263.py::test_bopla_patch_extra_fields_ignored

## [HIGH] fix T635 — XSS: Template name field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/serializers/played.py:37-40`
Next step: Add HTML sanitization for name field
Notes: |
  XSS vulnerability. Script tags and event handlers in template name are stored
  without sanitization. Potential stored XSS if rendered without escaping.
  Ref: test_playout_history_template_redteam_t263.py::test_xss_in_name_field

## [HIGH] fix T636 — XSS: Template type field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/serializers/played.py:37-40`
Next step: Add HTML sanitization or validation for type field
Notes: |
  XSS vulnerability. Script tags in template type field are stored without sanitization.
  Combined with name XSS allows multiple injection points.
  Ref: test_playout_history_template_redteam_t263.py::test_xss_in_type_field

## [MEDIUM] fix T637 — No rate limiting on Template CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/views/played.py:37-42`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. Template CREATE has no rate limiting.
  Rapid sequential requests (20) all succeed with 201. Can create template spam.
  Ref: test_playout_history_template_redteam_t263.py::test_rapid_template_creation

## [MEDIUM] fix T638 — No rate limiting on Template UPDATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/history/views/played.py:37-42`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. Template UPDATE has no rate limiting.
  Rapid sequential updates (20) all succeed with 200. Can cause update storms.
  Ref: test_playout_history_template_redteam_t263.py::test_rapid_template_updates

## [MEDIUM] fix T639 — BOPLA: TemplateField CREATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/serializers/played.py:43-46`
Next step: Add strict validation to reject unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. TemplateField CREATE accepts
  extra fields like "is_admin", "password", "role" and silently ignores them.
  Ref: test_playout_history_template_field_redteam_t264.py::test_bopla_create_extra_fields_ignored

## [MEDIUM] fix T640 — BOPLA: TemplateField PATCH accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/serializers/played.py:43-46`
Next step: Add strict validation on PATCH for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. TemplateField PATCH accepts
  extra fields like "is_system", "internal_flag" and silently ignores them.
  Ref: test_playout_history_template_field_redteam_t264.py::test_bopla_patch_extra_fields_ignored

## [CRITICAL] fix T641 — BOLA: TemplateField CREATE in other user's template
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/views/played.py:44-50`
Next step: Add template ownership validation in serializer
Notes: |
  API1:2023 Broken Object Level Authorization. CREATE TemplateField allows specifying
  any template_id regardless of ownership. Attacker can add fields to victim's template.
  Ref: test_playout_history_template_field_redteam_t264.py::test_bola_create_field_for_other_users_template

## [HIGH] fix T642 — XSS: TemplateField name field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/serializers/played.py:43-46`
Next step: Add HTML sanitization for name field
Notes: |
  XSS vulnerability. Script tags in field name are stored without sanitization.
  Potential stored XSS if rendered in frontend without escaping.
  Ref: test_playout_history_template_field_redteam_t264.py::test_xss_in_name_field

## [HIGH] fix T643 — XSS: TemplateField label field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/serializers/played.py:43-46`
Next step: Add HTML sanitization for label field
Notes: |
  XSS vulnerability. Script tags and event handlers in label field stored unsanitized.
  Ref: test_playout_history_template_field_redteam_t264.py::test_xss_in_label_field

## [LOW] fix T644 — Validation: TemplateField accepts negative position
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/serializers/played.py:43-46`
Next step: Add MinValueValidator(0) for position field
Notes: |
  Negative position values are accepted but don't make sense for field ordering.
  Should reject negative values with validation error.
  Ref: test_playout_history_template_field_redteam_t264.py::test_create_negative_position

## [MEDIUM] fix T645 — No rate limiting on TemplateField CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:55:00Z
Last worked: 2026-04-10T15:55:00Z
File: `app/api/api/history/views/played.py:44-50`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. TemplateField CREATE has no rate limiting.
  Rapid sequential requests (20) all succeed with 201. Can create field spam.
  Ref: test_playout_history_template_field_redteam_t264.py::test_rapid_field_creation

## [MEDIUM] fix T646 — BOPLA: ListenerCount CREATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/serializers/listener.py`
Next step: Add strict validation to reject unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. ListenerCount CREATE accepts
  extra fields like "is_admin", "station_id" and silently ignores them.
  Ref: test_listener_count_redteam_t265.py::test_bopla_create_extra_fields_ignored

## [CRITICAL] fix T647 — BOPLA: Can manipulate listener count statistics
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/serializers/listener.py`
Next step: Add validation to prevent arbitrary count manipulation
Notes: |
  API3:2023 Broken Object Property Level Authorization. UPDATE allows setting arbitrary
  listener_count values (e.g., 999999). Can fake statistics to show false popularity.
  Ref: test_listener_count_redteam_t265.py::test_bopla_update_listener_count_manipulation

## [LOW] fix T648 — Validation: Negative listener count accepted
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/serializers/listener.py`
Next step: Add MinValueValidator(0) for listener_count field
Notes: |
  Negative listener_count values are accepted but don't make sense.
  Should reject negative values with validation error.
  Ref: test_listener_count_redteam_t265.py::test_bopla_negative_listener_count

## [MEDIUM] fix T649 — No rate limiting on ListenerCount CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/views/listener.py`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. ListenerCount CREATE has no rate limiting.
  Rapid sequential requests (20) all succeed with 201. Can spam fake statistics.
  Ref: test_listener_count_redteam_t265.py::test_rapid_listener_count_creation

## [MEDIUM] fix T650 — Pagination missing on ListenerCount LIST
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/views/listener.py`
Next step: Add pagination to ListenerCountViewSet
Notes: |
  API4:2023 Unrestricted Resource Consumption. LIST returns all records without pagination.
  Large datasets (>100 records) returned in single response. Can cause DoS.
  Ref: test_listener_count_redteam_t265.py::test_bulk_listener_count_query

## [LOW] fix T651 — Validation: Future timestamp accepted for listener counts
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/serializers/listener.py`
Next step: Add validation to reject future timestamps
Notes: |
  Future timestamps are accepted but listener counts can't exist for future time.
  Should validate timestamp <= now().
  Ref: test_listener_count_redteam_t265.py::test_create_with_future_timestamp

## [LOW] fix T652 — Validation: End before start date range accepted
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/history/views/listener.py`
Next step: Add date range validation (end >= start)
Notes: |
  Query with end date before start date is accepted. Should return 400 for invalid range.
  Ref: test_listener_count_redteam_t265.py::test_end_before_start_date_range

## [MEDIUM] fix T653 — BFLA: Guest user can access live logs
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/views/live.py`
Next step: Add permission check to restrict guest access to live logs
Notes: |
  API5:2023 Broken Function Level Authorization. Guest users can LIST live logs.
  Should be restricted to authenticated users with appropriate permissions.
  Ref: test_live_log_redteam_t266.py::test_bola_guest_user_can_access_logs

## [MEDIUM] fix T654 — BOPLA: LiveLog CREATE accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/serializers/live.py:6-9`
Next step: Add strict validation to reject unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. LiveLog CREATE accepts
  extra fields like "is_admin", "station_id", "owner" and silently ignores them.
  Ref: test_live_log_redteam_t266.py::test_bopla_create_extra_fields_ignored

## [CRITICAL] fix T655 — BOPLA: Can fake stream end time
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/serializers/live.py:6-9`
Next step: Add validation to prevent arbitrary end_time manipulation
Notes: |
  API3:2023 Broken Object Property Level Authorization. UPDATE allows setting arbitrary
  end_time (e.g., 24 hours in future). Can fake stream duration for false analytics.
  Ref: test_live_log_redteam_t266.py::test_bopla_update_fake_end_time

## [LOW] fix T656 — Validation: LiveLog end_time before start_time accepted
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/serializers/live.py:6-9`
Next step: Add validation: end_time must be >= start_time
Notes: |
  end_time before start_time is accepted but creates impossible time ranges.
  Should validate temporal consistency.
  Ref: test_live_log_redteam_t266.py::test_bopla_end_time_before_start_time

## [LOW] fix T657 — Validation: Future start_time accepted for live logs
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/serializers/live.py:6-9`
Next step: Add validation to reject future start_time
Notes: |
  Future timestamps are accepted but live logs should represent past/current streams.
  Should validate start_time <= now().
  Ref: test_live_log_redteam_t266.py::test_bopla_future_start_time

## [MEDIUM] fix T658 — BOPLA: LiveLog PATCH accepts extra fields
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/serializers/live.py:6-9`
Next step: Add strict validation on PATCH for unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. PATCH accepts extra fields
  like "is_system", "internal" and silently ignores them.
  Ref: test_live_log_redteam_t266.py::test_bopla_patch_extra_fields_ignored

## [HIGH] fix T659 — XSS: LiveLog state field stored unsanitized
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/serializers/live.py:6-9`
Next step: Add HTML sanitization for state field
Notes: |
  XSS vulnerability. Script tags and event handlers in state field stored unsanitized.
  Potential stored XSS if rendered in analytics dashboard.
  Ref: test_live_log_redteam_t266.py::test_xss_in_state_field

## [MEDIUM] fix T660 — No rate limiting on LiveLog CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/views/live.py`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. LiveLog CREATE has no rate limiting.
  Rapid sequential requests (20) all succeed with 201. Can spam log entries.
  Ref: test_live_log_redteam_t266.py::test_rapid_live_log_creation

## [MEDIUM] fix T661 — Pagination missing on LiveLog LIST
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/views/live.py`
Next step: Add pagination to LiveLogViewSet
Notes: |
  API4:2023 Unrestricted Resource Consumption. LIST returns all records without pagination.
  Large datasets (>100 records) returned in single response. Can cause DoS.
  Ref: test_live_log_redteam_t266.py::test_bulk_live_log_list

## [MEDIUM] fix T662 — No rate limiting on LiveLog UPDATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T16:05:00Z
Last worked: 2026-04-10T16:05:00Z
File: `app/api/api/history/views/live.py`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. LiveLog UPDATE has no rate limiting.
  Rapid sequential updates (20) all succeed with 200. Can cause update storms.
  Ref: test_live_log_redteam_t266.py::test_rapid_updates


# Completed Tasks

## [DONE] test T267 — MountName LIST unit and redteam security tests
Completed: 2026-04-10T15:19:37Z
Summary: |
  Created 15 redteam security tests for MountName LIST endpoint.
  Tests cover: authorization (requires 'mountname' permission), SQL injection,
  information disclosure (ID enumeration), resource consumption (rate limiting, bulk),
  authentication bypass, HTTP method tampering, unicode/edge cases.
  All tests pass (15 passed).
  Files: `app/api/api/history/tests/views/test_mount_name_list_redteam_t267.py`

## [CRITICAL] fix T663 — BOLA: Podcast LIST shows all users' podcasts regardless of owner
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add owner-based queryset filtering in PodcastViewSet
Notes: |
  API1:2023 Broken Object Level Authorization. PodcastViewSet.queryset = Podcast.objects.all()
  without owner filtering. Any authenticated user can see ALL podcasts.
  Ref: test_podcast_list_redteam_t268.py::test_bola_t353_list_shows_all_users_podcasts

## [HIGH] fix T664 — BFLA: Guest user can access podcast LIST endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:25`
Next step: Restrict podcast permission to authenticated non-guest users
Notes: |
  API5:2023 Broken Function Level Authorization. Guest users (role=G) can list podcasts.
  Should require at least HOST role for LIST operations.
  Ref: test_podcast_list_redteam_t268.py::test_bola_t353_guest_user_can_list_podcasts

## [MEDIUM] fix T665 — BOLA: ID format confusion allows access manipulation
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add strict ID format validation (integer only)
Notes: |
  API1:2023 BOLA. Non-standard ID formats (1.0, trailing spaces, null bytes) may bypass checks.
  Ref: test_podcast_list_redteam_t268.py::test_bola_id_format_manipulation_numeric

## [MEDIUM] fix T673 — Information Disclosure: Owner ID exposed in LIST response
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Remove owner field from serializer or use SerializerMethodField with permission check
Notes: |
  API8:2023 Security Misconfiguration. Owner ID in response allows user enumeration attacks.
  Attacker can harvest all user IDs and target them individually.
  Ref: test_podcast_list_redteam_t268.py::test_list_includes_owner_id

## [MEDIUM] fix T675 — BOLA: IDOR via different status codes for existing vs non-existing
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Return 404 for both unauthorized and non-existent resources
Notes: |
  API1:2023 BOLA + API8:2023 Info Disclosure. Different errors (200 vs 404) allow ID enumeration.
  Regular user gets 200 for admin's podcast (BOLA!) vs 404 for non-existent.
  Ref: test_podcast_list_redteam_t268.py::test_id_enumeration_via_404_403

## [MEDIUM] fix T678 — No rate limiting on Podcast LIST endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. 50+ requests per second allowed without throttling.
  Can lead to DoS and resource exhaustion.
  Ref: test_podcast_list_redteam_t268.py::test_rapid_list_requests

## [MEDIUM] fix T679 — No pagination on Podcast LIST (100+ records returned)
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add pagination to PodcastViewSet
Notes: |
  API4:2023 Unrestricted Resource Consumption. All 100+ podcasts returned in single response.
  Large datasets cause memory exhaustion and slow responses.
  Ref: test_podcast_list_redteam_t268.py::test_bulk_podcast_list

## [CRITICAL] fix T682 — BOLA: PodcastEpisode LIST shows other users' private episodes
Status: NOT_STARTED
Created: 2026-04-10T15:25:00Z
Last worked: 2026-04-10T15:25:00Z
File: `app/api/api/podcasts/views/podcast.py:28-35`
Next step: Add owner-based filtering via podcast__owner in PodcastEpisodeViewSet
Notes: |
  API1:2023 Broken Object Level Authorization. EpisodeViewSet.queryset = PodcastEpisode.objects.all()
  without filtering by podcast__owner. Any user can see ALL episodes from ALL podcasts.
  Ref: test_podcast_list_redteam_t268.py::test_bola_episode_list_shows_all_episodes

## [MEDIUM] fix T703 — BOPLA: Podcast CREATE silently ignores extra/unknown fields
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add strict field validation to reject unknown fields
Notes: |
  API3:2023 Broken Object Property Level Authorization. CREATE accepts fields like
  "is_admin", "role", "internal" and silently ignores them. Should reject with 400.
  Ref: test_podcast_create_redteam_t269.py::test_bopla_extra_fields_ignored

## [MEDIUM] fix T706 — Information Disclosure: URL credentials stored in plaintext
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/models/podcast.py:12`
Next step: Strip credentials from URL or reject URLs with credentials
Notes: |
  API8:2023 Security Misconfiguration. URLs like http://admin:secret@host/ are stored
  with credentials visible. Information disclosure risk if DB compromised.
  Ref: test_podcast_create_redteam_t269.py::test_ssrf_url_with_credentials

## [HIGH] fix T708 — Stored XSS: Script tags in podcast title not sanitized
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add HTML sanitization for all text fields
Notes: |
  API8:2023 Injection. <script>alert(1)</script> in title stored without sanitization.
  Stored XSS vulnerability - executes when podcast displayed in admin UI.
  Ref: test_podcast_create_redteam_t269.py::test_stored_xss_in_title

## [HIGH] fix T709 — Stored XSS: Script tags in description not sanitized
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add HTML sanitization for description field
Notes: |
  API8:2023 Injection. Stored XSS in description field. Can steal cookies/session.
  Ref: test_podcast_create_redteam_t269.py::test_stored_xss_in_description

## [HIGH] fix T710 — Stored XSS: Script tags in iTunes metadata not sanitized
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add HTML sanitization for all iTunes fields
Notes: |
  API8:2023 Injection. Stored XSS in itunes_author, itunes_summary, itunes_subtitle.
  Ref: test_podcast_create_redteam_t269.py::test_stored_xss_in_itunes_fields

## [MEDIUM] fix T713 — No rate limiting on Podcast CREATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add Django Ratelimit or DRF throttling
Notes: |
  API4:2023 Unrestricted Resource Consumption. 30+ CREATE requests per second allowed.
  Can lead to DoS, database bloat, and resource exhaustion.
  Ref: test_podcast_create_redteam_t269.py::test_rapid_create_requests

## [MEDIUM] fix T721 — JavaScript URL scheme accepted (XSS vector)
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Validate URL scheme - allow only http/https
Notes: |
  API8:2023 Injection. javascript:alert(1) accepted as valid podcast URL.
  XSS vector - if URL is rendered as link, executes JavaScript.
  Ref: test_podcast_create_redteam_t269.py::test_invalid_url_formats

## [LOW] fix T722 — Race condition allows duplicate podcast creation
Status: NOT_STARTED
Created: 2026-04-10T15:40:00Z
Last worked: 2026-04-10T15:40:00Z
File: `app/api/api/podcasts/models/podcast.py:38-41`
Next step: Add unique constraint on URL field or use get_or_create
Notes: |
  API6:2023 Unrestricted Access to Sensitive Business Flows. Concurrent requests
  can create duplicate podcasts with same URL. No unique constraint in model.
  Ref: test_podcast_create_redteam_t269.py::test_duplicate_creation_race

## [CRITICAL] fix T727 — BOLA: Regular user can RETRIEVE admin's private podcast
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add owner-based permission check in retrieve()
Notes: |
  API1:2023 Broken Object Level Authorization. No ownership check on RETRIEVE.
  Regular users can access full details of any podcast including description.
  Ref: test_podcast_rud_redteam_t270.py::test_bola_retrieve_other_users_private_podcast

## [MEDIUM] fix T730 — BOPLA: PATCH silently ignores extra/unknown fields
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add strict field validation to reject unknown fields in PATCH
Notes: |
  API3:2023 Broken Object Property Level Authorization. PATCH accepts extra fields
  like "is_system", "internal_id" and silently ignores them.
  Ref: test_podcast_rud_redteam_t270.py::test_bopla_patch_extra_fields

## [HIGH] fix T732 — Stored XSS: Script tags in UPDATE title not sanitized
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add HTML sanitization for title in UPDATE
Notes: |
  API8:2023 Injection. <script> tags in title field stored without sanitization
  when updated via PUT. Stored XSS vulnerability.
  Ref: test_podcast_rud_redteam_t270.py::test_xss_via_update_title

## [HIGH] fix T733 — Stored XSS: Script tags in PATCH description not sanitized
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/podcasts/serializers/podcast.py`
Next step: Add HTML sanitization for description in PATCH
Notes: |
  API8:2023 Injection. <img onerror=> in description stored without sanitization
  when patched. Stored XSS vulnerability.
  Ref: test_podcast_rud_redteam_t270.py::test_xss_via_patch_description

## [MEDIUM] fix T735 — No rate limiting on Podcast UPDATE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add Django Ratelimit or DRF throttling for UPDATE
Notes: |
  API4:2023 Unrestricted Resource Consumption. 30+ UPDATE requests per second
  allowed without throttling. Can cause update storms and DoS.
  Ref: test_podcast_rud_redteam_t270.py::test_rapid_update_requests

## [MEDIUM] fix T736 — No rate limiting on Podcast DELETE endpoint
Status: NOT_STARTED
Created: 2026-04-10T15:50:00Z
Last worked: 2026-04-10T15:50:00Z
File: `app/api/api/podcasts/views/podcast.py:21-26`
Next step: Add Django Ratelimit or DRF throttling for DELETE
Notes: |
  API4:2023 Unrestricted Resource Consumption. 20+ DELETE requests per second
  allowed. Rapid deletion can cause data loss and DoS.
  Ref: test_podcast_rud_redteam_t270.py::test_rapid_delete_requests

## [MEDIUM] fix T740 — No account lockout after multiple failed login attempts
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/core/auth.py`
Next step: Implement account lockout after 5 failed attempts
Notes: |
  API2:2023 Broken Authentication. 10+ failed login attempts allowed without lockout.
  Brute force vulnerability - attacker can guess passwords indefinitely.
  Ref: test_auth_session_redteam_t279.py::test_brute_force_account_lockout

## [MEDIUM] fix T741 — Weak passwords accepted (123456, password, qwerty)
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/core/models/user.py`
Next step: Add password strength validator
Notes: |
  API2:2023 Broken Authentication. Common weak passwords like "123456", "password",
  "qwerty" are accepted. Should reject passwords from common wordlists.
  Ref: test_auth_session_redteam_t279.py::test_weak_password_accepted

## [MEDIUM] fix T742 — Common passwords from wordlists accepted
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/core/models/user.py`
Next step: Integrate password validator with haveibeenpwned or rockyou.txt
Notes: |
  API2:2023 Broken Authentication. Passwords like "password123", "iloveyou", "princess"
  from common wordlists are accepted. Should check against known compromised passwords.
  Ref: test_auth_session_redteam_t279.py::test_common_passwords_accepted

## [MEDIUM] fix T743 — Short passwords (< 8 chars) accepted
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/core/models/user.py`
Next step: Enforce minimum password length of 8 characters
Notes: |
  API2:2023 Broken Authentication. Passwords with less than 8 characters are accepted.
  NIST recommends minimum 8 characters for passwords.
  Ref: test_auth_session_redteam_t279.py::test_password_min_length

## [HIGH] fix T745 — BFLA: Guest user can access protected endpoints
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/api/permissions.py`
Next step: Restrict guest access to read-only endpoints only
Notes: |
  API5:2023 Broken Function Level Authorization. Guest users (role=G) can access
  endpoints like /api/v2/files, /api/v2/libraries that should be restricted.
  Ref: test_auth_session_redteam_t279.py::test_guest_user_access_restrictions

## [LOW] fix T746 — No limit on concurrent user sessions
Status: NOT_STARTED
Created: 2026-04-10T16:00:00Z
Last worked: 2026-04-10T16:00:00Z
File: `app/api/settings/_django.py`
Next step: Add SESSION_CONCURRENT_LIMIT or similar setting
Notes: |
  API2:2023 Broken Authentication. User can have unlimited concurrent sessions.
  Increases risk of session hijacking and makes session revocation difficult.
  Ref: test_auth_session_redteam_t279.py::test_concurrent_session_limit

## [CRITICAL] fix T749 — UnicodeEncodeError: API key header with unicode causes 500
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/api/permissions.py` or DRF authentication
Next step: Add try/except for unicode encoding errors, return 403 instead of 500
Notes: |
  API8:2023 Security Misconfiguration. Unicode characters in Authorization header
  cause UnicodeEncodeError: 'latin-1' codec can't encode characters. Server returns
  500 instead of 403. Information disclosure via stack trace.
  Ref: test_auth_apikey_redteam_t280.py::test_api_key_unicode_injection

## [MEDIUM] fix T750 — No rate limiting on API key authentication attempts
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/api/permissions.py`
Next step: Implement rate limiting for failed API key attempts
Notes: |
  API4:2023 Unrestricted Resource Consumption. 30+ API key attempts per second
  allowed without throttling. Brute force vulnerability for API key guessing.
  Ref: test_auth_apikey_redteam_t280.py::test_api_key_brute_force_detection

## [MEDIUM] fix T751 — API key format variations may cause unexpected errors
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/api/permissions.py`
Next step: Validate API key format strictly, reject malformed headers with 403
Notes: |
  API8:2023 Security Misconfiguration. Malformed Authorization headers like
  "Api-Key\nX-Injected: header" may cause unexpected behavior or header injection.
  Ref: test_auth_apikey_redteam_t280.py::test_api_key_format_variations

## [MEDIUM] fix T752 — Long API keys (>1000 chars) may cause DoS
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/api/permissions.py`
Next step: Add max length validation for API key (256 chars max)
Notes: |
  API4:2023 Unrestricted Resource Consumption. Very long API keys (10K+ chars)
  accepted without length limits. Potential memory exhaustion DoS.
  Ref: test_auth_apikey_redteam_t280.py::test_api_key_length_limits

## [MEDIUM] fix T753 — Case-sensitive Authorization header parsing
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/api/permissions.py` or DRF
Next step: Ensure header parsing is case-insensitive per HTTP spec
Notes: |
  API8:2023 Security Misconfiguration. Lowercase "authorization" header rejected
  with 403, though HTTP spec requires case-insensitive header names. Client
  compatibility issue.
  Ref: test_auth_apikey_redteam_t280.py::test_authorization_header_case_sensitivity

## [MEDIUM] fix T755 — API keys have no expiration (long-lived tokens)
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/settings/_libretime.py`
Next step: Implement API key rotation and expiration
Notes: |
  API2:2023 Broken Authentication. API keys from config never expire.
  If key is leaked, attacker has permanent access until config changed.
  Ref: test_auth_apikey_redteam_t280.py::test_api_key_no_expiration

## [LOW] fix T756 — API key can access user-specific endpoints
Status: NOT_STARTED
Created: 2026-04-10T16:40:00Z
Last worked: 2026-04-10T16:40:00Z
File: `app/api/api/permissions.py`
Next step: Restrict API key to service endpoints only
Notes: |
  API5:2023 Broken Function Level Authorization. API key (service token) can
  access user-specific endpoints like /api/v2/users. Should be restricted.
  Ref: test_auth_apikey_redteam_t280.py::test_api_key_vs_user_permissions

## [MEDIUM] fix T769 — No rate limiting on public endpoints
Status: NOT_STARTED
Created: 2026-04-10T16:55:00Z
Last worked: 2026-04-10T16:55:00Z
File: `app/api/api/views/info.py` and `app/api/api/views/version.py`
Next step: Add Django Ratelimit or middleware for public endpoints
Notes: |
  API4:2023 Unrestricted Resource Consumption. 100+ requests to /api/v2/info in under 5 seconds
  allowed without throttling. Can be used for DoS and resource exhaustion attacks.
  Ref: test_auth_public_redteam_t281.py::test_rapid_requests_no_rate_limit
