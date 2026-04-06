# Code style ledger

<!-- Protocol: ~/.config/kimi/skills/style-protocol/SKILL.md (modified: 2026-04-03T19:39:37Z, commit: d7b218d442ccc2d8229bbc567649af803b333b28)

Empirical patterns to **mirror** in project source. **Refs** = repo-relative **paths from repository root**. Does not replace reading **neighbors** in the same directory — supplements cross-session memory. Formatter/linter configs stay authoritative for auto-format; this file captures **human/project idioms** agents should copy.

Allocate **S<n>:** scan all `## S` headings for `## S<number> —`; next id = max **n** + 1 (never reuse). See **style-protocol**.
-->

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

<!--
## S1 — Short title
Status: ACTIVE
Created: YYYY-MM-DDTHH:mm:ssZ
Last touched: YYYY-MM-DDTHH:mm:ssZ
Refs: `path/under/repo/file.ext`
Observation:
- what to mimic (telegraphic EN)
Applies_to: optional `path/prefix/` or glob
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
