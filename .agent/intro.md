# libretime — Agent Context (via .agent/intro.md)

- This file modification datetime: 2026-04-06T16:54:33Z
- File modified at commit: 0b3458bb2371d1f9b865d57b6ab317559cb4a296

<!-- hub-settings-snapshot path=~/.config/kimi/prompts/settings.md commit=d7b218d442ccc2d8229bbc567649af803b333b28 modified=2026-04-03T19:39:37Z -->
<!-- The following section is a FULL COPY of hub settings, auto-updated on init/sync. Do not edit manually. -->
---
<!-- Protocol: ~/.config/kimi/prompts/settings.md
     Verify freshness (author date + hash of last commit touching this file):
     git -C ~/.config/kimi log -1 --format="%H %cI" -- prompts/settings.md
     After editing this file, commit the hub repo so the line above stays truthful. -->

# Kimi hub — mandatory agent settings

**Read in full:** at the **start** of every run of repo-init / repo-sync / repo-update, and at interactive session start when working from a generated `.agent/intro.md`. Reading only "the obvious bits" or one section is **wrong**—the whole file applies.

**Binding / supremacy:** everything written **in this file** is **mandatory**. No agent turn, user message, prompt, template, skill, protocol, or local project note may **contradict**, **override**, **waive**, or **reinterpret** it. If anything else conflicts with this file, **this file wins**. There are no exceptions "just this once".

**Authority:** same class as `~/.config/kimi/skills/*-protocol/SKILL.md`, but scoped to hub-wide **settings** (formats, path style, snapshot mechanics, and how they interact with other docs—see § Relation to Persist state).

**Duplication:** prefer **linking here** instead of copying rules. If another file repeats a rule, it must **match** this file; if wording diverges, treat **this file** as the source of truth.

Checkpoint *procedure* (when to run Persist state, primary `.agent/*` files — history, decisions, tasks, knowledge, style — plus **conditional** glossary; skip rules, report line) lives in **`~/.config/kimi/templates/agent.md`** § SKILLS → **Persist state** and in each repo's **`.agent/intro.md`** § SKILLS → *Persist state*. That procedure **must still obey** every applicable rule in **this file** (for example **Timestamps**, **Paths**, **Snapshot line**).

## Host model mandatory policies (outside hub prose)

The **running model's** non-waivable rules (provider / product safety, disallowed content, required disclosure of nature where applicable, harassment limits, etc.) apply **regardless** of stylistic prompts. Where **`~/.config/kimi/prompts/roleplay.md`** or a user message **conflicts** with those rules, **treat the conflicting fragment as void**: do **not** follow it, and **do not** re-litigate the skip in every reply (no standing disclaimer, no lecture) unless the **user explicitly asks** why something was omitted or softened.

This section does **not** relax **hub documentation** rules defined elsewhere in **this file** (timestamps, paths, snapshot, supremacy of this file for those topics).

---

## Timestamps (agent-written)

All **new** date+time strings agents write into `.agent/*`, templates they fill, and hub markdown must be:

- **Format:** ISO **8601** in **UTC**, fixed pattern `YYYY-MM-DDTHH:mm:ssZ`
  - Literal **`T`** between date and time
  - Literal **`Z`** = Zulu / UTC (no numeric offset, no bare local time)
- **Example:** `2026-04-03T19:41:14Z`
- **Reject:** `2026-04-03 19:41:14`, `2026-04-03T19:41:14+00:00` in **agent-produced** prose (git `%cI` snapshots in comments may still show `+00:00` — normalize to `Z` when **you** write files)
- **Shell (current instant, UTC):** `date -u +%Y-%m-%dT%H:%M:%SZ`

## On-disk language (agent-written)

**Scope:** Any content agents **write or rewrite** on disk: `.agent/*.md`, filled templates, `prompts/*.md` (hub operator text), `skills/**/*.md`, `templates/**`, commit messages if agent-authored, YAML / markdown bodies, task titles/summaries, history sessions, knowledge entries, checklist prose.

**Required style:**

- **English only** for agent-authored text — **no Cyrillic** (and no other non-English natural language) in persisted artifacts.
- **Telegraphic technical English:** drop articles where still clear; short clauses; prefer IT jargon (`repo`, `symlink`, `flush`, `checkpoint`, `allowlist`, `wiring`, `merge`, `span`).
- **Token discipline:** prefer symbols, paths, backticks, `T<n>` over long prose.

**Exceptions:**

- **Verbatim user quote** inside `"..."` when documenting what user said — keep original language inside quotes; wrap with English context.
- **`~/.config/kimi/prompts/roleplay.md`:** **do not edit** that file to satisfy this section — it defines **in-chat** voice / language / persona (Phase 0b). When it exists, agents **must** read it **in full** after **`settings.md`** and **apply** it to live replies (e.g. non-English with user); **disk** still obeys this section (see **`templates/agent.md`** / **`.agent/intro.md`** **AGENT_RULES**).
- **Third-party quotes, license headers, upstream identifiers** — leave unchanged.

**Migration:** On any touch of a file that still has non-English agent text, **replace** with English per this section; do not leave mixed-language agent prose.

## Paths in user-home catalog (documentation, agent text, and hub agent YAML)

For **any path under the user's home directory** when it appears in: prompts, templates, `.agent/*.md`, skill text, tables, blockquotes, and **`agents/*.yaml`** (including `system_prompt_path`) — use **tilde** form:

- **Required:** `~/.config/kimi/...`, `~/project/foo` (paths are **relative to home** in this notation, not repo-relative).
- **Forbidden in that context:** `/Users/<name>/...`, `/home/<name>/...`, `C:\Users\...`
- **`$HOME`:** avoid in **readable** markdown and in **YAML path string values**; use **`~`** so hub configs stay portable across machines. Exception: **shell one-liners** where the shell must expand a variable, e.g. `git -C "$HOME/.config/kimi" ...` — that is fine inside fenced `bash` command blocks.
- **Consumers** (e.g. kimi CLI loading `agents/*.yaml`) must expand **`~`** to the current user's home directory when resolving `system_prompt_path`.

---

## Snapshot line in generated `.agent/intro.md`

The template includes an HTML comment `<!-- hub-settings-snapshot ... -->` filled from:

`git -C ~/.config/kimi log -1 --format="%H %cI" -- prompts/settings.md`

When **writing** that line into `.agent/intro.md` (or template substitution), set `commit=` to the full hash (first field) and `modified=` to the same instant as git's `%cI` (second field), **normalized** to **`YYYY-MM-DDTHH:mm:ssZ`** per **§ Timestamps** — do not leave numeric offsets (`+03:00`, `+00:00`, etc.) in the snapshot's `modified=` value.

**repo-init** / **repo-sync** / **repo-update** must **refresh** that comment whenever they rewrite `.agent/intro.md` from the hub template logic.

---

## Relation to Persist state (checkpoints)

**Triggers, execution order, skip rules, and the standard user-facing report** are spelled out under **`### Persist state (checkpoints)`** inside **`## SKILLS`** in two parallel places: (1) **`~/.config/kimi/templates/agent.md`** — hub master text that **`repo-init`** copies or **`repo-sync`** merges from; (2) the target repository's **`.agent/intro.md`** — the same section layout after that repo has been initialized (not a different document "kind", just the per-repo instance). Protocol skills document **per-file** edits during that checkpoint.

Those procedural documents do **not** relax or replace anything in **this file**. While executing Persist state, agents still follow **all** of **settings.md** (e.g. how to write times and paths, how to refresh `hub-settings-snapshot`, **§ On-disk language**). The fifth unconditional checkpoint file is **`.agent/style.md`** (**style-protocol**). **`.agent/glossary.md`** (**glossary-protocol**) is written **only** when that skill's **Write gate** applies in the session.
<!-- END OF SETTINGS COPY -->

> **Full Location:** `.agent/intro.md` — **AGENTS.md** at the repository root is a symlink to this file (not the other way around).
> **Work History:** `.agent/history.md`
> **Active Decisions:** `.agent/decisions.md`
> **Codebase Knowledge:** `.agent/knowledge.md`
> **Code style ledger:** `.agent/style.md` (empirical; **style-protocol**)
> **Glossary:** `.agent/glossary.md` (user phrases → model meaning; **glossary-protocol**)

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
- `core` — users, auth, preferences, workers
- `storage` — files, libraries
- `schedule` — shows, playlists, smart blocks, webstreams
- `podcasts` — podcast management
- `history` — listener stats, playout history
- `legacy` — migrations from old schema

## CONVENTIONS
- **Hub settings:** read **`~/.config/kimi/prompts/settings.md` in full** — **supreme** and **non-overridable** for everything it states; do not contradict it elsewhere in this file.

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
- **Read `~/.config/kimi/prompts/settings.md` in full before substantive work** — **supreme** for all rules defined there (see `hub-settings-snapshot` in HTML comment above; refresh via git per that file). Nothing overrides it. **On-disk language:** English-only telegraphic prose per settings **§ On-disk language**.
- **Read and follow `~/.config/kimi/prompts/roleplay.md` when it exists** — load **in full** immediately after settings; **apply** to all live user-facing replies (tone, languages, register, persona, chat habits). Must not override settings, tool discipline, or checkpoint procedure; **§ On-disk language** still governs persisted files; fragments conflicting with host-model policies are void per settings **§ Host model mandatory policies**.
- **`.agent/style.md` + neighbors:** before **substantive project code** edits, read **`.agent/style.md`** (**style-protocol**) for ACTIVE **`S<n>`** notes and **Reference anchors**; always **mirror** adjacent files in the same package. **Append** or extend **`S<n>`** when you find repeatable idioms; **Refs** = repo-relative paths.
- **`.agent/glossary.md`:** read **in full** early when interpreting user instructions that may use project-specific phrasing (**glossary-protocol**). **Add or change** **`G<n>`** entries **only** when the user **explicitly** asks to record a term or definition — **not** from casual conversation or inference alone.
- **Respect .gitignore** — ignore all files/patterns listed in .gitignore (EXCEPT `.agent/` directory which must always be tracked)
- Do not run tests or linters without explicit request
- Do not refactor code without explicit request
- Use git only for read operations, never for write operations (e.g. commit, push, pull) without explicit request
- When in doubt, check .agent/decisions.md for active decisions
- Update .agent/tasks.md when starting/completing work items
- **Read `.agent/history.md` at session start** — check for recent context and active decisions before planning work
- **Persist state without being asked** — after non-trivial work, and when the user moves on within the same chat (e.g. "ok", "thanks", "next task", "next question"), run a **full checkpoint** (see **SKILLS** → *Persist state*). Do **not** wait only for explicit "save work" phrasing.
- **Update `.agent/history.md`** — append session entries per **memory-protocol**; checkpoints must land in history, not only in chat memory.
- **Keep `.agent/tasks.md` and `.agent/decisions.md` honest** — same checkpoint: sync task status and log any decisions taken (see task-protocol / decision-protocol).
- **`.agent/style.md` after code work** — reconcile **S<n>** notes on checkpoint when you touched project source (**style-protocol**); continuous capture during coding session encouraged.
- **Update `.agent/knowledge.md` autonomously and continuously** — write there **on your own** as you learn; the user should never have to ask to "remember" or "add to knowledge". Checkpoints add a structured **flush**, not permission to defer writes until then.
- **Read the corresponding protocol skill BEFORE modifying any `.agent/` file** — check the `<!-- Protocol: ... -->` comment at the top of the file for the exact path; each file contains a **FULL COPY** of its protocol between `<!-- The following section is a FULL COPY...` and `<!-- END OF PROTOCOL COPY -->` markers

## MEMORY_HINTS
- **Treat "next task / next question" as a checkpoint boundary** — one coherent unit of work should be reflected in `.agent/` before you start the next.
- **Knowledge grows by itself** — if you only touch knowledge.md when the user says "save", you are doing it wrong.
- **Glossary is gated** — **glossary.md** gets new **`G<n>`** rows **only** when the user explicitly author recording; do **not** "helpfully" define project jargon without that signal.
- Workspace uses `uv` for package management (not pip/poetry)
- Each `app/*` component is a separate package with its own pyproject.toml
- Legacy PHP code in `legacy/` should rarely be modified
- Services communicate via RabbitMQ message queue
- Playout can operate independently if API is down (schedule is cached)
- Not designed for multi-tenancy — one install per radio station

## SKILLS

> **Checkpoint vs settings:** **Persist state** below is the checkpoint *procedure*. **`~/.config/kimi/prompts/settings.md`** is read **in full** and is **supreme** for **everything** it defines; execution of Persist state **must comply** with it end-to-end.

The `.agent/` directory is the on-disk workspace for agents. **Each skill document defines exactly how to read and write one primary file.** Paths in the Protocol column assume the canonical skills live under `~/.config/kimi/skills/` (adjust if your hub is elsewhere).

### Connected protocol skills

| Kind | Primary file / use | Document |
|------|---------------------|----------|
| **Hub settings (read first, supreme)** | Entire file — binding, non-overridable | `~/.config/kimi/prompts/settings.md` |
| memory-protocol | `.agent/history.md` | `~/.config/kimi/skills/memory-protocol/SKILL.md` |
| decision-protocol | `.agent/decisions.md` | `~/.config/kimi/skills/decision-protocol/SKILL.md` |
| task-protocol | `.agent/tasks.md` | `~/.config/kimi/skills/task-protocol/SKILL.md` |
| knowledge-protocol | `.agent/knowledge.md` | `~/.config/kimi/skills/knowledge-protocol/SKILL.md` |
| style-protocol | `.agent/style.md` | `~/.config/kimi/skills/style-protocol/SKILL.md` |
| glossary-protocol | `.agent/glossary.md` | `~/.config/kimi/skills/glossary-protocol/SKILL.md` |

### How to use these protocols

- **Session start:** read **Hub settings** (`~/.config/kimi/prompts/settings.md`) **in full** (supreme); if `~/.config/kimi/prompts/roleplay.md` exists, read it **in full** next and **apply** to live replies (see **AGENT_RULES**); then each skill's **Read on Session Start** for the files you rely on (at minimum: history, tasks, decisions, **`.agent/glossary.md`**; often knowledge too; **`.agent/style.md`** before **project code** work).
- **Before editing any `.agent/*` file:** open the skill named in that file's `<!-- Protocol: ... -->` line and follow it end-to-end for that edit.
- **During work:** **knowledge-protocol** runs **continuously and on your own initiative** — no user prompt required; default action is WRITE.
- **After substantial work, when wrapping up, or when the user pivots:** run **Persist state** below — do not rely on the user to remember to ask.

### Persist state (checkpoints)

A **checkpoint** updates **all** of: `.agent/history.md`, `.agent/decisions.md`, `.agent/tasks.md`, **reconciles** `.agent/knowledge.md` (continuous writes should already exist; the knowledge skill describes any final flush), **reconciles** `.agent/style.md` (style-protocol; **S<n>** ledger), and **conditionally** **`.agent/glossary.md`** (**glossary-protocol** — **only** if the **Write gate** opened this session or edits are pending; otherwise no-op).

**Run a full checkpoint automatically** when any of the following is true:

- The user uses an explicit save phrase — e.g. "save work", "save progress", "checkpoint", or similar.
- The user closes a thread of work in-session — e.g. "ok", "thanks" + **a new ask**, or direct phrases like "next task", "next question", "what's next" in the sense of **switching** to another task or topic.
- You have finished a **non-trivial** deliverable (multi-step fix, design choice, investigation) even if the user immediately continues talking — persist **before** the next large step.

**Order** (concrete edits per file live only in that file's skill — open each **Save Work / Persist state** section):

1. **memory-protocol** — `.agent/history.md`
2. **decision-protocol** — `.agent/decisions.md`
3. **task-protocol** — `.agent/tasks.md`
4. **knowledge-protocol** — `.agent/knowledge.md`
5. **style-protocol** — `.agent/style.md`
6. **glossary-protocol** — `.agent/glossary.md` **if** **Write gate** or pending edits (else skip file touch)

If the user explicitly asked only for a quick factual answer and nothing was decided or tracked, you may skip a **full** checkpoint — but still update **knowledge.md** if you learned something non-obvious, and **style.md** if you made substantive code observations worth **`S<n>`**; run step 6 **only** if glossary was user-authorized this session.

**Report** after a full checkpoint: `Work saved: history updated, decisions logged, tasks synced, knowledge and style ledger reconciled; glossary reconciled if updated.`

## KNOWN_ISSUES
- Legacy codebase contains technical debt (Zend Framework 1, Propel ORM)
- Some tests may require Docker services (postgres, rabbitmq)
- Liquidsoap integration requires external binary

## EXTERNAL_RESOURCES
- Documentation: https://libretime.org/docs/
- Forum: https://discourse.libretime.org
- Matrix: #libretime:matrix.org
- C4 Process: https://rfc.zeromq.org/spec:42/c4/
- Conventional Commits: https://www.conventionalcommits.org/

---

*This file is maintained by repo-init-agent. Last full sync: 2026-04-06T16:54:33Z*
