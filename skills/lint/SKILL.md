---
description: Validate wiki page frontmatter schema and fix issues. Use when the user wants to check, validate, or fix wiki pages for schema compliance, broken links, or staleness.
---

# Lint Skill

Arguments: `$ARGUMENTS` (optional: specific page path to lint, default: all pages)

## Workflow

1. **Run lint**: Execute `loppy lint-frontmatter` to get JSON findings array.

2. **Filter** (if `$ARGUMENTS` provided): Keep only findings for pages matching the argument.

3. **Categorize findings**:
   - `missing_field`: Required frontmatter field absent
   - `bad_enum`: Field value not in allowed set
   - `stale`: Page not updated in >90 days
   - `orphan`: Page in index but file missing
   - `broken_link`: Wikilink target does not exist

4. **Report**: Show findings grouped by severity:
   - **Errors** (missing_field, bad_enum, orphan, broken_link): Must fix
   - **Warnings** (stale): Should review

5. **Offer to fix**: For each fixable issue (missing fields, bad enums, broken links), offer to apply corrections. Apply fixes with Write/Edit tool. Re-run `loppy lint-frontmatter` after fixing to confirm clean.

6. **Log**: Run `loppy log "Lint complete" "<N> issues found, <M> fixed"` after finishing.

If no findings, report "Wiki schema valid. No issues found."
