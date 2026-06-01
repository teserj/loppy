---
name: wiki-query
description: Query the wiki knowledge base to find and synthesize information. Use when the user wants to search, look up, or ask questions about knowledge stored in the wiki.
---

# Query Skill

Arguments: `$ARGUMENTS` (required: search term, tag, type filter, or domain filter)

If `$ARGUMENTS` is empty, ask the user what to search for.

## Workflow

1. **Load config**: Run `loppy config` to get wiki_dir path.

2. **Read index**: Read `<wiki_dir>/index.md` to get the page index.

3. **Search**: Find pages matching `$ARGUMENTS`:
   - Match against path, title, type, domain, tags (case-insensitive)
   - Filters: `type:<value>`, `domain:<value>`, `tag:<value>` narrow results
   - Plain terms match anywhere in path or title

4. **Fetch relevant pages**: Read up to 5 best-matching pages from wiki_dir.

5. **Synthesize**: Extract the relevant sections and provide a focused answer to what the user is looking for.

6. **Cite sources**: List which wiki pages the answer draws from, with their paths.

If no matches found, suggest related terms or report the wiki is empty.
