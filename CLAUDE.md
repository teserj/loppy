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
Used by `/wiki ingest` to show LLM what to process next.

### loppy move SOURCE
Move source file (absolute path) to `sources_dir/processed/`. If vault is git repo, uses git mv for history.
Used by LLM after ingesting a source to mark it as processed.

### loppy index-merge
Read JSON stdin `[{path, summary}, ...]` and merge into `index.md`.
- Reads existing TSV index
- Upserts entries (path is key)
- Detects orphans (pages in wiki not in input)
- Atomically writes updated index
Used by `/wiki ingest` after creating new pages.

### loppy log
Append timestamped entry to `log.md` with ISO 8601 timestamp.
Prepends newest entry (newest-first ordering).
Used by `/wiki ingest` and `/wiki lint` to record operations.

### loppy lint-frontmatter
Validate all wiki pages (except index.md, log.md).
Checks:
- Required fields: type, title, created, updated, confidence, domain, tags, links
- Enum validation: type, domain, confidence
- Staleness: confidence=stale if updated >90 days ago
- Orphans: path in index but page not found
- Broken links: wikilink targets don't exist
Returns JSON array of findings: `[{path, field, issue}, ...]`

## Slash Commands

### /wiki ingest [mode] [count]
**Mode**: single (default) or batch
**Count**: number of sources (batch only, default: batch_size)

Workflow:
1. List next N unprocessed sources (`loppy next`)
2. Display to LLM with guidance
3. LLM reads source content (Read tool)
4. LLM creates wiki page with schema-compliant frontmatter
5. LLM updates index.md via `loppy index-merge` (stdin JSON)
6. LLM moves source via `loppy move`
7. LLM appends log entry via `loppy log`

### /wiki query <term>
Search wiki by keyword, tag, type, or domain.
1. Read index.md
2. Filter by term match (case-insensitive)
3. Display matching pages
4. LLM can fetch and synthesize answers

### /wiki lint [page]
Validate wiki schema.
1. Run `loppy lint-frontmatter`
2. Filter by page (optional)
3. Display findings
4. LLM can fix issues

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

**Config must exist**: Plugin fails gracefully if `~/.config/loppy/config.json` missing.

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
- `tests/commands/`: /wiki slash command tests
- `tests/docs/`: Documentation tests

**E2E protocol** (manual or CI):
1. Run setup.py with test vault paths
2. Place test source in sources_dir/
3. Ingest via /wiki ingest single
4. Verify page created in wiki/
5. Query via /wiki query and verify results
6. Run /wiki lint and verify no errors
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
