# Loppy — Design Spec

**Date:** 2026-04-17
**Status:** Approved for planning

## 1. Purpose

Loppy is a Claude Code plugin that owns a Karpathy-style LLM wiki: a persistent, LLM-maintained knowledge base compiled from raw sources. It provides the scaffolding (setup, schema, starter files) and the three canonical operations (`ingest`, `query`, `lint`) via a single `/wiki` slash command. Retrieval tooling today = `wiki/index.md` + file read; the design leaves a clean swap point for future backends (e.g., `qmd` MCP).

References:
- Karpathy original gist: `~/.vault/wiki/sources/llm-wiki-karpathy.md`
- Gökçe implementation: `~/.vault/wiki/sources/llm-wiki-gokce.md`
- Synthesized concept page: `~/.vault/wiki/concepts/llm-wiki-pattern.md`

## 2. Architecture

Four logical layers:

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code (LLM layer)                                │
│  /wiki slash command  ──── Write/Edit/Bash tools        │
└────────────┬──────────────────────────┬─────────────────┘
             │                          │
  ┌──────────┴──────────┐   ┌───────────▼──────────────┐
  │  Schema layer       │   │  Guard layer (hooks)     │
  │  wiki-schema.yaml   │   │  guard-vault.sh          │
  │  CLAUDE.md          │   │  PreToolUse:             │
  │  (plugin-level)     │   │   Bash → block rm/mv/…   │
  └─────────────────────┘   │   Write → block empty    │
             │              │          writes to vault │
             │              └───────────┬──────────────┘
             ▼                          │ allowlist:
  ┌──────────────────────┐              │  loppy *, git mv/rm
  │  Mechanics layer     │              │
  │  loppy (bash)        │◀─────────────┘
  │  config|next|move|   │
  │  index-merge|log|    │
  │  lint-frontmatter    │
  └──────────┬───────────┘
             │ reads/writes
             ▼
  ┌──────────────────────┐
  │  Data layer (vault)  │
  │  sources/ processed/ │
  │  wiki/ index.md …    │
  └──────────────────────┘
```

### Plugin repo layout

```
loppy/
├── .claude-plugin/plugin.json
├── commands/wiki.md
├── bin/loppy
├── hooks/
│   ├── hooks.json
│   └── guard-vault.sh
├── templates/
│   ├── wiki-schema.yaml
│   ├── index.md
│   └── log.md
├── setup.sh
├── CLAUDE.md
└── README.md
```

### Runtime state

- **Config:** `~/.config/loppy/config.json` (XDG). Survives plugin reinstalls.
- **Vault:** user-chosen `VAULT_DIR` (default `~/.vault`). Holds `sources/`, `sources/processed/`, `wiki/`, `wiki/wiki-schema.yaml`, `wiki/index.md`, `wiki/log.md`, plus `<namespace>/*.md` pages.

### Invariants

1. Plugin code never edits the vault directly. Only `bin/loppy` (bash) and `/wiki` (LLM, via Write/Edit) touch vault contents.
2. LLM never runs destructive shell ops against the vault. Enforced structurally by `guard-vault.sh`, not prompt-advised.
3. `Write` with empty content into the vault is blocked by the same guard (prevents accidental truncation).
4. Only deletion paths allowlisted through the guard: `loppy <subcmd>` (trusted helper) and `git mv | git rm` (history-preserving, recoverable).
5. `setup.sh` is idempotent. Re-running on an initialized vault only refreshes `wiki-schema.yaml` with user confirmation.
6. Raw source files move from `sources/` to `sources/processed/` only after their wiki pages are written and `index.md` is updated. A mid-ingest crash leaves sources in place to retry.
7. No parallel writes to the wiki in a single vault (Gökçe's lesson — parallel agents corrupt files). Documented in `CLAUDE.md` as a user discipline; not enforced.

## 3. Components

Nine units, each with one purpose.

### 3.1 `setup.sh` — one-time initializer

- Prompts for `VAULT_DIR` (default `~/.vault`), `sources` subdir (default `sources`), `wiki` subdir (default `wiki`), `batch_size` (default 5).
- Writes `~/.config/loppy/config.json` (creates parent dir if missing).
- If `VAULT_DIR` is not a git repo, prompts `git init? [Y/n]`.
- Creates `$sources/processed/` if missing.
- Copies `templates/wiki-schema.yaml` → `$VAULT_DIR/wiki/wiki-schema.yaml`, confirming before overwrite of an existing file.
- If `$VAULT_DIR/wiki/index.md` or `log.md` missing, copies from templates. Never overwrites existing non-empty files.
- Idempotent. Depends on: `coreutils`, `git`, `jq`.

### 3.2 `.claude-plugin/plugin.json` — Claude Code plugin manifest

- Declares plugin `name: loppy`, `version`, `commands` dir, `hooks` dir.
- Consumed by Claude Code at plugin install.

### 3.3 `commands/wiki.md` — `/wiki <op>` slash command prompt

- Frontmatter: `argument-hint: ingest|query|lint [args]`.
- Body: structured Markdown prompt that tells the LLM to:
  - Always start with `loppy config` to load paths.
  - Branch on `$ARGUMENTS` into the ingest / query / lint workflow (see §4).
  - Use `bin/loppy` helpers for mechanical ops.
  - Use `Write`/`Edit` for wiki page writes.
- References `bin/loppy` via `${CLAUDE_PLUGIN_ROOT}/bin/loppy` so it works without PATH modification.

### 3.4 `bin/loppy` — bash helper

Single script, subcommand dispatcher. **Pure bash — no LLM, no API keys, no model dependency.**

| Subcommand | Input | Output | Purpose |
|---|---|---|---|
| `config [key]` | optional key | JSON blob or scalar value | Read config. Exit 1 if missing/malformed. |
| `next [N]` | optional N (default from config) | absolute paths, one per line | List up to N unprocessed source files. Excludes `processed/`. |
| `move <file>` | absolute path | — | Move source into `processed/` via `git mv` if repo, else `mv`. Refuses if dest exists. |
| `index-merge` | stdin JSON `[{path, summary}…]` | — (stderr: orphan warnings) | Upsert into `wiki/index.md`, re-sort, refresh count, bump `updated:`. Atomic write. |
| `log <op> <title>` | stdin = body | — | Prepend `## [YYYY-MM-DD] op \| title` block to `wiki/log.md`. |
| `lint-frontmatter` | — | JSON findings array | Scan every wiki `.md`, parse frontmatter, emit errors (missing fields, bad enums, broken links) and warnings (stale >90d, orphan not in index). |
| `--help` | — | usage text | Subcommand reference. |

Depends on: `jq`, `awk`, `find`, `git`, POSIX shell.

### 3.5 `hooks/hooks.json` + `hooks/guard-vault.sh` — guard layer

- `hooks.json`: registers `PreToolUse` matcher on tools `Bash` and `Write`.
- `guard-vault.sh`: reads tool input on stdin, loads `vault_dir` from config.
  - For `Bash`: if command matches destructive verbs (`rm`, `shred`, `rmdir`, `unlink`, `mv`, `dd`) AND references a vault path, block unless allowlisted (`loppy *`, `git mv|rm`).
  - For `Write`: if target path is inside vault AND content is empty or whitespace-only, block.
  - Block = exit 2 with stderr message the LLM sees.
  - Config missing: fail-open with stderr warning (can't know what to protect).
- Configured as required hook so hook failures surface loudly.

### 3.6 `templates/wiki-schema.yaml` — schema definition

Machine-parseable YAML. Defines:
- Allowed `type` values: `entity`, `concept`, `source`, `project`, `thought`, `todo`, `worklog`.
- Allowed `domain` values: `tech`, `finance`, `business`, `work`, `career`, `hobbies`, `family`, `parenting`, `relationships`, `self`.
- Allowed `confidence` values: `high`, `medium`, `low`, `stale`.
- Required frontmatter fields per type.
- Namespace → `type` mapping (files under `wiki/concepts/` must have `type: concept`, etc.).
- Link format rules (`[[wiki/<namespace>/<slug>]]`).

Read by: LLM (loaded into `/wiki` context), `loppy lint-frontmatter` (parses for enum validation). Lives at `$VAULT_DIR/wiki/wiki-schema.yaml` after setup so it's git-tracked with the wiki.

### 3.7 `templates/index.md`, `templates/log.md` — starter files

Minimal stubs with correct frontmatter and section headers so the first ingest has something to merge into.

### 3.8 `CLAUDE.md` — plugin-level agent guidance

Short, targets the LLM reader:
- Three-layer architecture summary.
- Guard hook behavior and allowlist.
- When to use `/wiki` vs direct file access.
- "Never parallelize wiki writes" rule (Gökçe's lesson).
- How to discover config (read `~/.config/loppy/config.json` or call `loppy config`).

### 3.9 `README.md` — human install + usage

Install instructions, setup.sh walk-through, command reference.

### Future stub

`/wiki query` retrieval is designed so its search step is swappable. v1 reads `wiki/index.md` + Glob/Read directly. When `qmd` MCP or similar lands, add a config key `retrieval_backend: index|qmd|...` and branch inside the slash command prompt. No architectural change required.

## 4. Data flow

### 4.1 `/wiki ingest` (batch)

```
1. /wiki prompt loads.
2. LLM → Bash: `loppy config`
   → {vault_dir, sources_dir, wiki_dir, batch_size: 5}
3. LLM → Bash: `loppy next 5`
   → 5 absolute paths (or empty).
4. For each source path:
   a. LLM → Read source file.
   b. LLM → Read wiki/index.md + wiki/wiki-schema.yaml (once at start of batch).
   c. LLM decides: new page vs update; which namespaces touched.
   d. LLM → Write/Edit wiki pages (target 5–15 page touches per source).
      - New source page in wiki/sources/.
      - New/updated concept, entity, topic pages as needed.
      - Frontmatter per wiki-schema.yaml.
5. LLM builds JSON payload of {path, summary} for every page touched in step 4.
6. LLM → Bash: `echo '<json>' | loppy index-merge`
   - Upsert, re-sort, recount, atomic write-back.
   - Orphan warnings on stderr → LLM addresses them, re-calls (bounded to 1 retry).
7. LLM → Bash: `loppy log ingest "batch (N sources)" <<< '<body>'`
8. For each source processed successfully:
   LLM → Bash: `loppy move <path>`   (git mv → processed/)
9. LLM summarizes to user: N sources ingested, M pages touched.
```

Single-entry ingest: same flow with `loppy next` replaced by a specific user-supplied path.

### 4.2 `/wiki query "<question>"`

```
1. LLM → Bash: `loppy config`
2. LLM → Read wiki/index.md.
3. LLM scans index by keyword + namespace → candidates.
4. LLM → Read candidates in parallel.
5. LLM synthesizes answer, cites via [[wiki/...]] links.
6. LLM offers to file answer as a new wiki page → if yes, fall through
   to single-entry ingest with source = the Q&A.
```

Swap point: step 3. `retrieval_backend` config key selects between built-in index scan and future backends.

### 4.3 `/wiki lint`

```
1. LLM → Bash: `loppy config`
2. LLM → Bash: `loppy lint-frontmatter`
   → JSON array of findings per file.
3. LLM groups by severity.
4. Errors (mechanical): propose fixes to user.
   - missing domain → LLM infers from tags/content, confirms.
   - broken link → suggest match or propose removal.
5. Warnings (stale >90d): present list, user chooses per page:
   - flip confidence: stale (frontmatter edit).
   - refresh (fall through to single-entry ingest for that page).
   - leave alone.
6. Judgment layer (LLM-only, no helper):
   - cross-ref density check.
   - spot-check pages for consistency with current sources.
   - flag duplicates or contradictions.
7. For each fix applied → Write/Edit the page, then:
   Bash: `loppy index-merge` (if summary changed).
   Bash: `loppy log lint "..." <<< '<body>'`
```

Non-destructive by default. All fixes proposed, user confirms.

### Cross-cutting flow properties

- Every `Bash` call passes through `guard-vault.sh`.
- `wiki/index.md`: read at start of ingest and query; written only by `loppy index-merge`.
- `wiki/log.md`: append-only; touched only by `loppy log`.
- Single-threaded per vault, per session.

## 5. Error handling

### Config / setup

- **Config missing.** `loppy config` exit 1: `loppy: config not found. Run setup.sh first.` `/wiki` surfaces verbatim.
- **Malformed JSON.** `jq` error bubbled up — same pattern, "re-run setup.sh."
- **Paths in config don't exist.** Start-of-run check aborts with specific missing path.

### Ingest

- **Source unreadable** (perms, encoding): skip, log stderr, continue batch. Final summary lists skipped.
- **Invalid frontmatter on new wiki page.** End-of-batch `loppy lint-frontmatter` over touched files blocks `loppy move`. Sources stay for retry.
- **`index-merge` orphan warnings.** Not an error. LLM writes missing summaries, re-invokes. Bounded to 1 retry, then surface.
- **`loppy move` fails** (dest exists, git conflict). Single file fails; others continue. LLM reports unmoved sources.
- **Crash mid-ingest.** Automatic recovery on next `/wiki ingest`: unmoved sources re-surface via `loppy next`. Wiki pages stay. Worst case: duplicate index entries, caught by next `/wiki lint`.

### Query

- **`wiki/index.md` missing.** Hard stop. User runs setup.sh or restores from git.
- **Broken `[[wiki/...]]` link.** LLM flags, offers to drop or TODO. `lint-frontmatter` catches too.
- **No relevant pages.** LLM says so, offers to file the Q&A.

### Lint

- **YAML parse failure on a page.** Error-level finding for that file; continue scanning others.
- **`wiki-schema.yaml` missing.** Fall back to built-in default enum set (compiled into the bash script). Warn user.

### Guard hook

- **False positive** on a legitimate call. LLM sees the stderr, adjusts. Persistent pattern → add to allowlist.
- **Hook script broken.** Configured as required → fail loudly. User sees clear error, can disable via `hooks.json` while fixing.
- **Config missing at hook time.** Fail-open with warning (blocking every Bash call worse than no guard).

### Cross-cutting

- **Two sessions same vault.** No locking in v1. `index-merge` atomic write prevents `index.md` corruption; log entries could interleave. Documented as "don't" in CLAUDE.md.
- **Vault not a git repo.** `loppy move` falls back to `mv`. Guard still allowlists deletions but no recovery. setup.sh warns.
- **Disk full / write fails.** Tool error bubbles up. LLM reports to user. Atomic writes prevent partial state.

**Principle:** prefer visible failure over silent repair. LLM is never told to "just retry," except the bounded orphan retry.

## 6. Testing

### Deterministic (CI)

**`bin/loppy`** — bats-core (or shell harness). Per subcommand:
- `config`: missing → exit 1; valid → prints JSON; key → scalar.
- `next N`: empty dir → zero lines; `processed/` excluded; N honored.
- `move`: git repo → `git mv`; non-git → `mv`; dest exists → refuses; source preserved.
- `index-merge`: fixture + stdin JSON → matches golden; orphan → stderr warning; atomic under SIGKILL.
- `log`: prepended; date format correct; idempotent; body preserved.
- `lint-frontmatter`: fixture vault with seeded problems → expected findings.

**`guard-vault.sh`** — stdin JSON feed, assert exit code + stderr:
- `rm -rf <vault>/foo` → 2, blocked.
- `loppy move <vault>/foo` → 0.
- `git mv <vault>/a <vault>/b` → 0.
- `Write` empty to vault path → 2.
- `rm -rf /tmp/x` → 0 (not vault).
- Config missing → 0, stderr warning.

**`setup.sh`** — throwaway temp dirs:
- Fresh run → config, `processed/`, schema, index, log created.
- Re-run → prompts preserved; existing files not clobbered without confirm.
- Non-git `VAULT_DIR` → prompts; `y` → `.git/` exists.

**`plugin.json` / `hooks.json`** — `jq` type checks against CC plugin schema.

### Non-deterministic (manual, shipped as `tests/manual.md`)

`commands/wiki.md` is an LLM prompt — no unit test possible. Replace with fixture-based e2e protocol:

1. Run `setup.sh` against `tests/fixtures/vault/` (seeded with 3 sample sources, empty wiki).
2. Run `/wiki ingest` in Claude Code.
3. Assert via `loppy lint-frontmatter` (deterministic over LLM output):
   - Every source produces `wiki/sources/<name>.md`.
   - Required frontmatter present per type.
   - `wiki/index.md` has entries for all new pages.
   - `wiki/log.md` has a new entry with today's date + `ingest` prefix.
   - Sources moved to `processed/`.
   - No broken `[[...]]` links.
4. `/wiki query "<seeded question>"` → LLM cites ≥1 fixture page.
5. `/wiki lint` on intentionally-corrupted fixture → expected findings.

Because the e2e *assertions* run through `loppy lint-frontmatter`, they inherit that component's test rigor — LLM nondeterminism is contained.

### CI pipeline

GitHub Actions on push: install bats-core + jq, run bash tests, validate manifests. No Claude Code in CI. Prompt file gets a lint-only pass (argument-hint present, no TODOs, expected `loppy` subcommand references).

### Layout

```
tests/
├── loppy/          bats for bin/loppy
├── guard/          bats for the hook
├── setup/          bats for setup.sh
├── fixtures/vault/ seeded vault for e2e
└── manual.md       e2e protocol
```

## 7. Out of scope / future

- Locking for concurrent sessions. v1 documents as a user discipline.
- Programmatic retrieval backend (`qmd` MCP, vector search). Swap point reserved in `/wiki query`; config key `retrieval_backend` to be added when needed.
- Cross-vault support. v1 assumes one vault per machine; re-running `setup.sh` points at a different vault (overwrites config).
- Automatic staleness refresh. v1 surfaces stale pages in lint; user triggers refresh manually.
- Programmatic YAML validator. v1 uses built-in `lint-frontmatter` bash logic; move to a proper YAML library if schema grows.

## 8. Open decisions — none

All decisions taken during brainstorming are baked into this spec.
