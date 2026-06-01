---
name: wiki-ingest
description: Ingest raw sources from the vault into structured wiki pages. Use when the user wants to process, import, or ingest source files into the wiki.
---

# Ingest Skill

Read the user's request to determine mode:
- No mode specified or "single" → ingest 1 source
- "batch" → ingest batch_size sources (from config)
- "batch N" → ingest N sources

## Workflow

1. **Load config**: Run `loppy config` to get vault paths and batch_size.

2. **List sources**: Run `loppy next <count>` to get unprocessed sources. Output is one **absolute path per line** (e.g. `/home/user/vault/sources/Agentic AI Notes.md`). If empty, report "No unprocessed sources found" and stop.

3. **For each source file** (use the exact absolute path from step 2):
   a. Read the file content
   b. Extract key knowledge: facts, concepts, entities, relationships
   c. Create a wiki page at `wiki/<type>/<slug>.md` with this exact frontmatter:
      ```yaml
      ---
      type: <entities|concepts|sources|projects|thoughts|todos|worklogs>
      title: "<descriptive title>"
      created: <YYYY-MM-DD>
      updated: <YYYY-MM-DD>
      confidence: <high|medium|low>
      domain: <tech|finance|business|work|career|hobbies|family|parenting|relationships|self>
      tags: [tag1, tag2]
      links: [wiki/path/to/related-page]
      ---
      ```
   d. Write the page body below the frontmatter with clean, structured markdown.
   e. Update the index: pipe JSON to `loppy index-merge`:
      ```bash
      echo '[{"path":"wiki/<type>/<slug>.md","summary":"<one-line summary>"}]' | loppy index-merge
      ```
   f. Move source to processed — pass the **exact absolute path** from step 2, one argument only:
      ```bash
      loppy move "/home/user/vault/sources/Agentic AI Notes.md"
      ```
      Destination is always `sources_dir/processed/` — do NOT pass a second argument.
   g. Log the operation: `loppy log "Ingested <title>" "Created wiki/<type>/<slug>.md from <source>"`

4. **Summary**: Report how many pages were created and any issues.
