# Loppy

Personal knowledge management plugin implementing Karpathy's LLM Wiki pattern for Claude Code.

Ingest raw sources (articles, papers, links) into a structured wiki, then query and refine your knowledge using LLM-driven workflows.

## Quick Start

### Installation

1. Install Loppy plugin in Claude Code
2. Run interactive setup:
   ```bash
   ./setup.sh
   ```
3. Follow prompts for:
   - Vault directory path (e.g., `~/my-vault`)
   - Sources directory (default: `source`)
   - Wiki directory (default: `wiki`)
   - Git initialization (optional)

### First Ingest

1. Place a raw source (article, link, text) in your `sources/` directory
2. In Claude Code, run:
   ```
   /wiki ingest single
   ```
3. Follow LLM guidance to:
   - Review the source
   - Create a structured wiki page
   - Update the index
   - Move source to `processed/`

## Usage

### Ingest Sources

```
/wiki ingest [mode] [count]
```

**Single mode** (default): Ingest one source at a time
```
/wiki ingest single
```

**Batch mode**: Ingest multiple sources at once
```
/wiki ingest batch 5
```

### Query Knowledge

```
/wiki query <term>
```

Search your wiki by keyword, tag, type, or domain:
```
/wiki query machine learning
/wiki query type:concepts
/wiki query domain:tech
```

### Validate Schema

```
/wiki lint [page]
```

Check all wiki pages for schema compliance:
```
/wiki lint                  # Check all pages
/wiki lint wiki/topics/llm  # Check specific page
```

## Architecture

### Three-Layer Design

**Sources**: Raw input files (minimal structure)
- Articles, papers, links, notes
- Stored in `sources/` directory
- Moved to `processed/` after ingestion

**Wiki**: Compiled knowledge with strict schema
- Markdown pages with YAML frontmatter
- Stored in `wiki/` directory
- Each page has: type, title, created, updated, confidence, domain, tags, links

**Schema**: Frontmatter structure
- Defines required fields and valid values
- Enforced by `loppy lint-frontmatter`
- Enables AI and humans to work together reliably

### Data Flow

```
[Raw Source] 
    ↓
[LLM Read + Analysis]
    ↓
[Create Wiki Page with Frontmatter]
    ↓
[Update index.md]
    ↓
[Move to processed/]
    ↓
[Log operation]
```

### File Structure

```
vault-dir/
├── sources/           # Raw sources before ingestion
├── processed/         # Ingested sources (archive)
├── wiki/              # Compiled wiki pages
│   ├── index.md       # Page index (auto-updated)
│   ├── log.md         # Operation audit log
│   ├── wiki-schema.yaml  # Frontmatter schema
│   └── topics/
│       ├── machine-learning.md
│       └── llm-patterns.md
├── .git/              # Optional git repo
└── config.json        # (Backed up, edited via setup.sh)
```

## Configuration

Config stored in `~/.config/loppy/config.json`:

```json
{
  "vault_dir": "/home/user/my-vault",
  "sources_dir": "/home/user/my-vault/sources",
  "wiki_dir": "/home/user/my-vault/wiki",
  "batch_size": 5
}
```

Edit by running `setup.sh` again or manually editing the JSON file.

## Commands Reference

| Command | Purpose |
|---------|---------|
| `loppy config` | Display current configuration |
| `loppy next N` | List N unprocessed sources |
| `loppy move SRC DEST` | Move source to processed/ |
| `loppy index-merge` | Update index.md from stdin JSON |
| `loppy log TITLE DETAILS` | Append entry to log.md |
| `loppy lint-frontmatter` | Validate all wiki pages |

## Frontmatter Schema

Every wiki page must have YAML frontmatter:

```yaml
---
type: concepts
title: "LLM-Managed Knowledge Graphs"
created: 2026-04-18
updated: 2026-04-18
confidence: high
domain: tech
tags: [llm, knowledge-management, pkm]
links: [wiki/concepts/llm-wiki-pattern, wiki/entities/karpathy]
---

# Page content in markdown...
```

**Required fields**:
- `type`: entities, concepts, sources, projects, thoughts, todos, worklogs
- `title`: Human-readable title
- `created`: ISO 8601 date (YYYY-MM-DD)
- `updated`: ISO 8601 date
- `confidence`: high, medium, low, stale (stale auto-detected if >90 days old)
- `domain`: tech, finance, business, work, career, hobbies, family, parenting, relationships, self
- `tags`: List of keywords
- `links`: List of wikilinks to related pages

## Troubleshooting

### Config not found

Run `setup.sh` to create `~/.config/loppy/config.json`

### No sources showing

Check that:
1. Sources exist in `sources/` directory
2. They are `.md` or `.txt` files
3. They haven't been moved to `processed/` already

### Lint errors

Run `/wiki lint` to see specific issues:
- Missing required fields
- Invalid enum values
- Links to non-existent pages
- Pages not updated in >90 days

### Git history lost

Always use `loppy move` (which calls git mv) instead of direct `mv` commands.

## Design Principles

- **Schema-driven**: Strict frontmatter ensures data consistency
- **Audit trail**: Append-only log records all operations
- **Git-friendly**: All changes can be committed with full history
- **LLM-native**: Structured data enables AI to query and update reliably
- **Human-readable**: Markdown format and TSV index are easy to read
- **Fail-safe**: Guard hook prevents accidental destructive commands

## Inspiration

Based on Andrej Karpathy's [LLM-Managed Knowledge Graphs](https://gist.github.com/karpathy/8703956) pattern, adapted for Claude Code and extended with Gökçe's L1/L2 cache optimization.

## License

Apache 2.0
