# Loppy — Agent Instructions

Personal knowledge management plugin implementing Karpathy's LLM Wiki pattern.
Ingest raw sources into a structured wiki, then query and validate knowledge.

## Setup

Config lives at `~/.config/loppy/config.json` (XDG). Run `loppy config` to inspect:

```json
{
  "vault_dir": "/path/to/vault",
  "sources_dir": "/path/to/vault/source",
  "wiki_dir": "/path/to/vault/wiki",
  "batch_size": 5
}
```

If config missing, run `python setup.py` first.

## CLI Reference (`bin/loppy`)

| Command | Description |
|---|---|
| `loppy config [key]` | Print config (or single key value) |
| `loppy next [N]` | List next N unprocessed source files (absolute paths, one per line) |
| `loppy move <src>` | Move source to `processed/` subdir (use this, not `mv`) |
| `loppy index-merge` | Read JSON stdin `[{path, summary}]`, upsert into `wiki/index.md` |
| `loppy log <title> <detail>` | Prepend timestamped entry to `wiki/log.md` |
| `loppy lint-frontmatter` | Validate all wiki pages; returns JSON findings array |

**Never use `rm`, `mv`, `rmdir` on vault paths directly.** Use `loppy move` and `loppy log` instead.

## Workflows

### Ingest Sources

User intent: "ingest", "process sources", "import"

1. Run `loppy config` to get paths and `batch_size`.
2. Read `<vault_dir>/wiki-schema.yaml` to get the current frontmatter schema (required fields and valid enum values).
3. Run `loppy next <count>` — prints absolute paths of unprocessed sources.
   - If empty, report "No unprocessed sources found" and stop.
4. For each source path:
   a. Read the file content.
   b. Extract key knowledge: facts, concepts, entities, relationships.
   c. Create `wiki/<type>/<slug>.md` with frontmatter matching the schema exactly.
   d. Update index:
      ```bash
      echo '[{"path":"wiki/<type>/<slug>.md","summary":"<one-line summary>"}]' | loppy index-merge
      ```
   e. Move source (pass exact absolute path from step 3, no second arg):
      ```bash
      loppy move "/absolute/path/to/source.md"
      ```
   f. Log:
      ```bash
      loppy log "Ingested <title>" "Created wiki/<type>/<slug>.md from <source>"
      ```
5. Report pages created and any issues.

### Query Wiki

User intent: "search", "find", "look up", "what do I know about"

1. Run `loppy config` to get `wiki_dir`.
2. Read `<wiki_dir>/index.md`.
3. Filter entries matching the search term (case-insensitive) against path, title, type, domain, tags.
   - Prefix filters: `type:<value>`, `domain:<value>`, `tag:<value>`
4. Read up to 5 best-matching pages.
5. Synthesize a focused answer and cite source page paths.

If no matches, suggest related terms or report the wiki is empty.

### Lint Wiki

User intent: "lint", "validate", "check schema", "fix frontmatter"

1. Run `loppy lint-frontmatter` — returns JSON array `[{path, field, issue}]`.
2. If a specific page was requested, filter findings to that page.
3. Categorize:
   - **Errors** (must fix): `missing_field`, `bad_enum`, `orphan`, `broken_link`
   - **Warnings** (should review): `stale`
4. For fixable issues, apply corrections by editing the file.
5. Re-run `loppy lint-frontmatter` to confirm clean.
6. Log: `loppy log "Lint complete" "<N> issues found, <M> fixed"`

If no findings, report "Wiki schema valid. No issues found."
