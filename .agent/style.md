# Code style ledger

<!-- Protocol: ~/.config/kimi/skills/style-protocol/SKILL.md (modified: 2026-04-07T12:03:05Z, commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7) -->
<!-- The following section is a FULL COPY of ~/.config/kimi/skills/style-protocol/SKILL.md
     Protocol commit: 8407a3fffae7e8a6a45e80fb73eeded8078dafa7
     Protocol modified: 2026-04-07T12:03:05Z -->
---
name: style-protocol
description: Protocol for maintaining .agent/style.md empirical code-style ledger (refs + observations)
---

# Style Protocol

Ledger of **empirical** project code style: what to **mirror** when writing/editing project source (naming, comment habits, error shapes, test layout, etc.). **Not** a dump of linter config — formatters enforce mechanics; this file captures **patterns agents should copy** from real neighbors, with **repo-relative** `Refs`.

## Style note identity

Each note has:

- **`S<n>`** — global id: literal **`S`** + decimal integer, **no leading zeros** (`S1`, `S12`). **One sequence per repository.** **`n` never decreases and is never reused** when a note is completed or cancelled (same immutability spirit as `T<n>` in task-protocol).

**Canonical heading (H2):**

```markdown
## S<n> — Short title
```

**Body fields** (order flexible; include all that apply):

```markdown
Status: ACTIVE | DONE | CANCELLED
Created: YYYY-MM-DDTHH:mm:ssZ
Last touched: YYYY-MM-DDTHH:mm:ssZ
Refs: `path/under/repo/a.ext`, `path/b.ext`
Observation:
- telegraphic bullets — what to mimic
Applies_to: optional `glob/` or path prefix this note is about
```

For **DONE**, add `Completed: …` and short `Summary:` when moving to **# Completed style notes**.

### Allocating the next `S<n>`

1. Read **all** of `.agent/style.md` (**# Active style notes**, **# Completed style notes**, any stray `## S` lines).
2. Collect every **`S` + digits** in an H2 line matching `## S<n> —`.
3. **`max`** = maximum numeric part; **next id** = `S{max + 1}` (or **`S1`** if none).
4. **Never** reuse a number.

## File structure

```
repo-root/
└── .agent/
    └── style.md           # Empirical code-style ledger
```

## Read on Session Start

1. **When you will edit, add, or review project source code** (any non-`.agent/` path under the repo): read **`.agent/style.md`** before writing patches — at least **# Reference anchors** and **all `Status: ACTIVE` notes** whose `Applies_to` matches the area you touch (if absent, read all ACTIVE notes; use **Refs** as secondary anchors).
2. **Still read neighboring source files** in the same package/directory — the ledger **supplements** local mirroring, does not replace it.
3. Acknowledge briefly: "Style ledger: N active notes, M anchors" (optional).

## Write triggers (mandatory when coding)

**During any session with substantive code work:**

- After you notice a **repeatable** pattern not already captured (or under-captured), **append** a new **`S<n>`** or extend an existing note's **Observation** / **Refs** (update **`Last touched`**).
- Prefer **Refs** with **2+ files** when the pattern is structural; one file is OK for rare isolated idioms.
- **Do not** log trivia formatters fix alone unless the team's **pre-format** habit matters (e.g. import grouping conventions not auto-fixed).

## Completing / cancelling

- **DONE:** move the whole `## S<n> — …` block to **`# Completed style notes`**; set `Status: DONE`, add **`Completed`** + **`Summary`**.
- **CANCELLED:** move to Completed (or keep in Active with `Status: CANCELLED` + reason in **Observation**) — **do not** reuse **`n`**.

## Save Work / Persist state (this protocol only)

When a **checkpoint** runs (triggers and order: **`~/.config/kimi/templates/agent.md`** or **`.agent/intro.md`** § SKILLS → *Persist state*), this protocol's **sole** responsibility is **`.agent/style.md`**.

1. Ensure **ACTIVE** notes reflect what you learned this session (**Observation** / **Refs** / **Applies_to** / **`Last touched`**).
2. Move finished notes to **Completed** per above.
3. **Do not** delete historical **DONE** notes — ledger is append-only except corrections.

This step runs **after** **knowledge-protocol** in the template order (fifth file). **glossary-protocol** (sixth) runs **after** this step **only when** its **Write gate** fired or `.agent/glossary.md` was edited.

## Hygiene

- **Repo-relative `Refs`** only — no secrets, no machine-specific paths.
- **Respect .gitignore** — do not point **Refs** at ignored paths unless the user explicitly works there.
- **English** in **Observation** / **Summary** / titles per hub **§ On-disk language**.

## Example

```markdown
## S1 — HTTP handler error JSON shape
Status: ACTIVE
Created: 2026-04-03T20:00:00Z
Last touched: 2026-04-03T20:15:00Z
Refs: `src/api/handlers/foo.ts`, `src/api/handlers/bar.ts`
Observation:
- errors return `{ error: string, code: string }` not thrown bare strings
- log line prefix `[api]` before `logger.error`
Applies_to: `src/api/handlers/`
```
<!-- END OF PROTOCOL COPY -->

## Reference anchors

<!--
Representative files agents should skim when entering an area (2–8 paths). Example:
- `src/main.rs` — binary entry
- `tests/integration/foo.rs` — integration test layout
-->

- `app/api/api/manage.py` — Django management entry
- `app/api/api/settings/base.py` — Django settings pattern
- `app/playout/playout/main.py` — Playout CLI entry
- `app/api/api/core/models.py` — Django model pattern
- `app/playout/playout/player/schedule.py` — Playout schedule logic
- `src/sdk/` — Shared utilities structure

# Active style notes

## S5 — Test isolation: cleanup order and ID assumptions
Status: ACTIVE
Created: 2026-04-09T21:03:16Z
Last touched: 2026-04-09T21:03:16Z
Refs: `app/api/api/storage/tests/views/test_library_create.py`, `app/api/api/storage/tests/views/test_file_delete_not_found.py`
Observation:
- Delete related objects before parent to avoid FK constraint errors
  File.objects.all().delete()  # First
  Library.objects.all().delete()  # Second
- Don't assume auto-increment IDs are predictable in full suite runs
- Use very large IDs (9999999999999) for "non-existent" resource tests
- Full suite may create thousands of records before your test runs
Applies_to: `app/api/**/tests/**`

## S4 — Test isolation: unique values for unique fields
Status: ACTIVE
Created: 2026-04-09T21:03:16Z
Last touched: 2026-04-09T21:03:16Z
Refs: `app/api/api/storage/tests/views/test_file_list.py`, `app/api/api/schedule/tests/views/test_show_list.py`
Observation:
- Never use hardcoded strings for fields with unique constraints in tests
- Use uuid for unique field values: `f"prefix_{uuid.uuid4().hex[:8]}"`
- Common unique fields: User.username, Library.code, Show.name (if unique)
- Transaction rollback between tests is not perfect — tests may share DB state
Applies_to: `app/api/**/tests/**`

## S3 — model_bakery timezone-aware datetime configuration
Status: ACTIVE
Created: 2026-04-09T21:03:16Z
Last touched: 2026-04-09T21:03:16Z
Refs: `app/api/api/conftest.py`, `app/api/api/schedule/tests/views/test_show_instance_update.py`
Observation:
- model_bakery generates naive datetime by default for DateTimeField
- Configure globally in conftest.py: `baker.generators.add('DateTimeField', lambda: timezone.now())`
- Or pass explicit: `baker.make(Model, starts_at=timezone.now())`
- Django warns: "DateTimeField received a naive datetime while time zone support is active"
Applies_to: `app/api/**/tests/**`

## S2 — Datetime formatting in API tests
Status: ACTIVE
Created: 2026-04-09T21:03:16Z
Last touched: 2026-04-09T21:03:16Z
Refs: `src/sdk/sdk/datetime.py`, `app/api/api/schedule/tests/views/test_show_instance_update.py`
Observation:
- Use `format_datetime(dt)` from `sdk.datetime` for all timezone-aware datetime formatting
- Never use `.isoformat().replace('+00:00', 'Z')` — helper does this internally
- Never use `now().isoformat()` — use `format_datetime(now())` instead
- Format: ISO 8601 with 'Z' suffix (UTC), seconds precision: `2026-03-26T12:14:56Z`
Applies_to: `app/api/**/tests/**`

## S6 — DRF APIClient auth override for security testing
Status: ACTIVE
Created: 2026-04-10T22:08:00Z
Last touched: 2026-04-10T22:08:00Z
Refs: `app/api/api/tests/test_credentials_vs_defaults.py`, `app/api/api/tests/test_schedule_invalid_token_redteam_t575_t584_t589_t597_t600.py`
Observation:
- credentials() has priority over defaults[] — use credentials() for auth override
- WRONG: client.defaults['HTTP_AUTHORIZATION'] = 'Bearer invalid' (doesn't override)
- CORRECT: client.credentials(HTTP_AUTHORIZATION='Bearer invalid')
- For fresh auth state, create new APIClient() instead of modifying existing
- Critical for redteam tests — false positive if auth not actually overridden
Applies_to: `app/api/**/tests/**`
-->

# Completed style notes

<!--
When done:
## S1 — Short title
Status: DONE
Created: YYYY-MM-DDTHH:mm:ssZ
Last touched: YYYY-MM-DDTHH:mm:ssZ
Completed: YYYY-MM-DDTHH:mm:ssZ
Summary: why retired / superseded
Refs: `...`
Observation:
- ...
-->


## S7 — Security validators pattern
Status: ACTIVE
Created: 2026-04-11T03:00:00Z
Last touched: 2026-04-11T03:00:00Z
Refs: `app/api/api/validators/`, `app/api/api/schedule/serializers/webstream.py`
Observation:
- Centralize security validators in `api/validators/` directory
- Each validator module focuses on one attack class: path.py, url.py, xss.py
- Validators raise ValidationError with descriptive message
- Use in serializers via extra_kwargs: `{"field": {"validators": [func]}}`
- Or override validate_field() for custom logic
- Pattern: `validate_<field>(self, value) -> validated_value`
Applies_to: `app/api/**/serializers/**`

## S8 — XSS validation patterns
Status: ACTIVE
Created: 2026-04-11T03:00:00Z
Last touched: 2026-04-11T03:00:00Z
Refs: `app/api/api/validators/xss.py`, `app/api/api/schedule/serializers/show.py`
Observation:
- Use regex-based detection for XSS patterns (script tags, event handlers)
- Block at API boundary (serializer validation), not template layer
- Two validator functions: validate_name_safe() for titles, validate_description_safe() for descriptions
- Pattern covers: <script>, onerror=, javascript:, data:text/html, entities
- Returns 400 error immediately on detection
Applies_to: `app/api/**/serializers/**`

## S9 — SecureModelSerializer inheritance
Status: ACTIVE
Created: 2026-04-11T03:00:00Z
Last touched: 2026-04-11T03:00:00Z
Refs: `app/api/api/serializers.py`, `app/api/api/storage/serializers/file.py`
Observation:
- Use SecureModelSerializer as base for all model serializers
- Provides mass assignment protection out of box
- Blocks: id manipulation, owner assignment, timestamp manipulation
- Rejects extra/unknown fields
- Apply field-specific validators in Meta.extra_kwargs
Applies_to: `app/api/**/serializers/**`

