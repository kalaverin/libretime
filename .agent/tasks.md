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
