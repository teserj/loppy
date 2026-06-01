# Loppy for Claude Code

## Scope

Loppy is a personal knowledge management plugin implementing Karpathy's LLM Wiki pattern. It provides:

- **Vault management**: Base directory for all knowledge (Obsidian-compatible)
- **Source ingestion**: Import raw sources (articles, papers, links)
- **Wiki compilation**: Transform sources into structured wiki with frontmatter schema
- **Knowledge retrieval**: Query wiki by keyword, tag, type, domain
- **Schema validation**: Ensure wiki pages follow standards (required fields, relationships)
- **Operation audit trail**: Append-only log of all changes

## Design

### Three-Layer Architecture

1. **Sources** (`sources_dir`): Raw input files (markdown, text) with minimal structure
2. **Wiki** (`wiki_dir`): Compiled knowledge with strict YAML frontmatter schema
3. **Schema** (`wiki-schema.yaml`): Defines frontmatter structure and valid values

### Data Model

**Vault Directory** (`vault_dir`)
- `<sources_dir>/`: Raw source files (user uploads here; path set in config)
- `<sources_dir>/processed/`: Sources already ingested
- `<wiki_dir>/`: Compiled wiki pages with frontmatter
  - `index.md`: Index of all pages (auto-updated by `loppy index-merge`)
  - `log.md`: Append-only operation log (updated by `loppy log`)
- `wiki-schema.yaml`: Frontmatter schema template

**Config** (`~/.config/loppy/config.json`)
```json
{
  "vault_dir": "/path/to/vault",
  "sources_dir": "/path/to/vault/sources",
  "wiki_dir": "/path/to/vault/wiki",
  "batch_size": 5
}
```

## Bin Commands

All commands map to `bin/loppy <subcommand>`:

### loppy config
Display current configuration. No side effects.

### loppy next [N]
List next N unprocessed sources from `sources_dir` (excludes `processed/` subdir).
Used by ingest workflow to show LLM what to process next.

### loppy move SOURCE
Move source file (absolute path) to `sources_dir/processed/`. If vault is git repo, uses git mv for history.
Used by LLM after ingesting a source to mark it as processed.

### loppy index-merge
Read JSON stdin `[{path, summary}, ...]` and merge into `index.md`.
- Reads existing TSV index
- Upserts entries (path is key)
- Detects orphans (pages in wiki not in input)
- Atomically writes updated index
Used by ingest workflow after creating new pages.

### loppy log
Append timestamped entry to `log.md` with ISO 8601 timestamp.
Prepends newest entry (newest-first ordering).
Used by ingest and lint workflows to record operations.

### loppy lint-frontmatter
Validate all wiki pages (except index.md, log.md).
Checks:
- Required fields: type, title, created, updated, confidence, domain, tags, links
- Enum validation: type, domain, confidence
- Staleness: confidence=stale if updated >90 days ago
- Orphans: path in index but page not found
- Broken links: wikilink targets don't exist
Returns JSON array of findings: `[{path, field, issue}, ...]`

## Workflows

Invoke by describing intent naturally. Claude Code reads this file and follows the workflow.

### Ingest
User intent: "ingest", "process sources", "import" — mode: single (default) or batch [N]

1. Run `loppy next <count>` to list unprocessed sources (absolute paths).
2. Read each source file.
3. Create wiki page at `wiki/<type>/<slug>.md` with schema-compliant frontmatter.
4. Update index: `echo '[{"path":"...","summary":"..."}]' | loppy index-merge`
5. Move source: `loppy move "/absolute/path/to/source.md"`
6. Log: `loppy log "Ingested <title>" "Created wiki/<type>/<slug>.md from <source>"`

### Query
User intent: "search", "find", "look up", "what do I know about"

1. Run `loppy config` to get `wiki_dir`.
2. Read `<wiki_dir>/index.md`.
3. Filter by search term (case-insensitive) against path, title, type, domain, tags.
4. Read up to 5 matching pages and synthesize a focused answer.
5. Cite source page paths.

### Lint
User intent: "lint", "validate", "check schema", "fix frontmatter" — optional: specific page path

1. Run `loppy lint-frontmatter` → JSON array `[{path, field, issue}]`.
2. Filter by page if requested.
3. Report errors (missing_field, bad_enum, orphan, broken_link) and warnings (stale).
4. Fix issues by editing files directly. Re-run to confirm clean.
5. Log: `loppy log "Lint complete" "<N> issues found, <M> fixed"`

## Guard Hook (guard_vault.py)

**Event**: PreToolUse
**Tools**: bash
**Behavior**: Intercepts Bash tool calls and blocks destructive patterns:
- `rm`, `rmdir`, `shred`, `unlink` targeting vault paths → BLOCK
- `mv` within vault (not git mv) → BLOCK
- `dd` on vault paths → BLOCK

**Allowlist**:
- `git mv` / `git rm` (history-preserving)
- `loppy *` commands (safe by design)
- All non-bash tools (read, write, etc.)

**Rationale**: Prevents accidental vault corruption from LLM-generated commands.

## Critical State

**Config must exist**: Loppy fails gracefully if `~/.config/loppy/config.json` missing.

**Vault structure assumed**:
- `sources_dir/` exists and contains raw files
- `wiki_dir/` exists and contains compiled pages with frontmatter
- `index.md` exists (created by setup.py)
- `log.md` exists (created by setup.py)
- `wiki-schema.yaml` exists (created by setup.py)

**Page path uniqueness**: Wiki pages identified by relative path from wiki_dir. No two pages should have same path.

**Frontmatter required**: All wiki pages must have YAML frontmatter block (---..---) with all required fields.

**Links format**: Wikilinks as `[text](wiki/category/page)` must exist in wiki_dir. `loppy lint-frontmatter` validates.

## Testing

**Unit tests** (`tests/`):
- `tests/loppy/`: Bin command tests
- `tests/guard/`: Guard hook tests
- `tests/templates/`: Template tests
- `tests/setup/`: setup.py tests
- `tests/commands/`: workflow tests
- `tests/docs/`: Documentation tests

**E2E protocol** (manual or CI):
1. Run setup.py with test vault paths
2. Place test source in sources_dir/
3. Run ingest workflow
4. Verify page created in wiki/
5. Run query workflow and verify results
6. Run lint workflow and verify no errors
7. Verify index.md and log.md updated

## Key Guidelines for LLM Operation

1. **Always respect schema**: Generate frontmatter matching wiki-schema.yaml exactly
2. **Use loppy commands**: Don't mv/rm directly; use `loppy move` and `loppy log`
3. **Maintain relationships**: Update index.md and log.md alongside page creation
4. **Query before ingesting**: Check what's already in wiki before creating duplicates
5. **Validate before committing**: Run `loppy lint-frontmatter` before final git commit
6. **Preserve git history**: Use `git mv` / `git rm` via `loppy move`, not direct shell commands

## Integration Points

- **Config**: `~/.config/loppy/config.json` (XDG standard)
- **Vault**: Obsidian-compatible directory structure
- **CLI**: All commands exposed via `bin/loppy`
- **Schema**: YAML frontmatter on all wiki pages
- **Index**: TSV format for programmatic access
- **Log**: Markdown append-only for human readability and git audit trail
