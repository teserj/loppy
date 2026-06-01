# Loppy

Personal knowledge management plugin implementing Karpathy's LLM Wiki pattern.
Works with **Claude Code** and **Codex CLI**.

Ingest raw sources (articles, papers, links) into a structured wiki, then query and refine your knowledge using LLM-driven workflows.

## Quick Start

### Installation

```bash
git clone https://github.com/teserj/loppy.git
cd loppy
python setup.py
```

Follow prompts for:
- Vault directory path (e.g., `~/my-vault`)
- Sources directory (default: `source`)
- Wiki directory (default: `wiki`)
- Git initialization (optional)

Setup installs the `loppy` binary to `~/.local/bin/` and writes hooks for both Claude Code and Codex CLI.
Ensure `~/.local/bin` is in your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Claude Code

Run Claude Code from your vault directory:

```bash
cd ~/my-vault
claude
```

Claude Code picks up `CLAUDE.md` and `skills/` automatically. Use slash commands:

```
/wiki ingest single
/wiki query <term>
/wiki lint
```

### Codex CLI

Run Codex from your vault directory:

```bash
cd ~/my-vault
codex
```

Codex picks up `AGENTS.md` and `skills/` automatically. Guard hook is registered globally at `~/.codex/hooks.json`.
Invoke skills explicitly or describe intent naturally:

```
$wiki-ingest
Ingest my next source into the wiki
```

## Usage

### Ingest Sources

**Claude Code**:
```
/wiki ingest [mode] [count]
/wiki ingest single
/wiki ingest batch 5
```

**Codex** — describe intent naturally:
```
Ingest the next 3 sources
Process my sources in batch
```

### Query Knowledge

**Claude Code**:
```
/wiki query <term>
/wiki query machine learning
/wiki query type:concepts
/wiki query domain:tech
```

**Codex** — ask naturally:
```
What do I know about machine learning?
Find concepts tagged with llm
```

### Validate Schema

**Claude Code**:
```
/wiki lint [page]
/wiki lint                  # all pages
/wiki lint wiki/topics/llm  # specific page
```

**Codex**:
```
Lint the wiki
Check wiki/topics/llm for schema errors
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
├── source/            # Raw sources before ingestion
├── processed/         # Ingested sources (archive)
├── wiki/              # Compiled wiki pages
│   ├── index.md       # Page index (auto-updated)
│   ├── log.md         # Operation audit log
│   └── topics/
│       ├── machine-learning.md
│       └── llm-patterns.md
├── wiki-schema.yaml   # Frontmatter schema
└── .git/              # Optional git repo
```

Config stored separately at `~/.config/loppy/config.json` (XDG).

## Configuration

`~/.config/loppy/config.json`:

```json
{
  "vault_dir": "/home/user/my-vault",
  "sources_dir": "/home/user/my-vault/source",
  "wiki_dir": "/home/user/my-vault/wiki",
  "batch_size": 5
}
```

Re-run `python setup.py` or edit the JSON directly to change paths.

## Commands Reference

| Command | Purpose |
|---------|---------|
| `loppy config` | Display current configuration |
| `loppy next [N]` | List N unprocessed sources (absolute paths) |
| `loppy move <src>` | Move source to `processed/` subdir |
| `loppy index-merge` | Update index.md from stdin JSON |
| `loppy log <title> <detail>` | Prepend entry to log.md |
| `loppy lint-frontmatter` | Validate all wiki pages, return JSON findings |

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

Run `python setup.py` to create `~/.config/loppy/config.json`.

### No sources showing

Check that:
1. Sources exist in `sources/` directory
2. They are `.md` or `.txt` files
3. They haven't been moved to `processed/` already

### Lint errors

Run `/wiki lint` (Claude Code) or ask Codex to lint:
- Missing required fields
- Invalid enum values
- Links to non-existent pages
- Pages not updated in >90 days

### Git history lost

Always use `loppy move` (which calls `git mv`) instead of direct `mv` commands.

## Design Principles

- **Schema-driven**: Strict frontmatter ensures data consistency
- **Audit trail**: Append-only log records all operations
- **Git-friendly**: All changes can be committed with full history
- **LLM-native**: Structured data enables AI to query and update reliably
- **Human-readable**: Markdown format and TSV index are easy to read
- **Fail-safe**: Guard hook prevents accidental destructive commands

## Inspiration

Based on Andrej Karpathy's [LLM-Managed Knowledge Graphs](https://gist.github.com/karpathy/8703956) pattern, adapted for Claude Code and Codex CLI, extended with Gökçe's L1/L2 cache optimization.

## License

Apache 2.0
