# Loppy End-to-End Test Protocol

Manual testing guide for Loppy plugin functionality.

## Prerequisites

- Claude Code installed
- Loppy plugin installed
- Fresh test environment (new vault recommended)

## Test 1: Setup and Configuration

**Goal**: Verify vault initialization and config creation.

1. Run: `./setup.sh`
2. Enter test vault path (e.g., `/tmp/loppy-test-vault`)
3. Use defaults: `source` and `wiki`
4. Skip git init for now (answer `n`)
5. Verify:
   - `~/.config/loppy/config.json` exists
   - Vault contains `source/`, `wiki/`, `wiki-schema.yaml`, `index.md`, `log.md`
   - Config JSON has correct paths and batch_size=5

**Expected output**:
```
=== Setup Complete ===
Vault: /tmp/loppy-test-vault
Sources: source
Wiki: wiki
Config: ~/.config/loppy/config.json

Next steps:
1. Place raw source files in: /tmp/loppy-test-vault/source/
...
```

## Test 2: Single Source Ingest

**Goal**: Verify single-source ingestion workflow.

1. Create test source:
   ```bash
   cat > $VAULT/source/test-article.md <<EOF
   # Test Article
   
   This is a sample article about machine learning.
   EOF
   ```

2. In Claude Code, run: `/wiki ingest single`

3. LLM should:
   - List the source
   - Read its content
   - Propose wiki page structure
   - Create page at `wiki/test-article.md` with frontmatter
   - Run `loppy index-merge` to update index
   - Run `loppy move test-article.md processed` to mark as done
   - Run `loppy log` to record operation

4. Verify end state:
   - `wiki/test-article.md` exists with frontmatter
   - `source/processed/test-article.md` exists
   - `wiki/index.md` contains entry for test-article
   - `wiki/log.md` has operation record

## Test 3: Batch Ingest

**Goal**: Verify batch ingestion of multiple sources.

1. Create 3 test sources in `source/`:
   ```bash
   cat > $VAULT/source/article-1.md <<EOF
   # Article 1
   Content here.
   EOF
   cat > $VAULT/source/article-2.md <<EOF
   # Article 2
   Content here.
   EOF
   cat > $VAULT/source/article-3.md <<EOF
   # Article 3
   Content here.
   EOF
   ```

2. In Claude Code, run: `/wiki ingest batch 3`

3. Verify:
   - All 3 sources listed
   - LLM processes each one
   - All 3 wiki pages created
   - All 3 moved to processed/
   - Index contains all 3 entries

## Test 4: Query Knowledge

**Goal**: Verify wiki search functionality.

1. Run: `/wiki query machine learning`

2. Verify:
   - Index searched for keyword
   - Matching pages listed
   - LLM can fetch and read pages

3. Test domain filter:
   - `/wiki query type:sources` (find all source pages)
   - `/wiki query domain:tech` (find all tech domain pages)

## Test 5: Validate Schema

**Goal**: Verify frontmatter validation.

1. Create a malformed page:
   ```bash
   cat > $VAULT/wiki/bad-page.md <<EOF
   ---
   type: sources
   title: "Missing Fields"
   ---
   
   Content but no created/updated/confidence/domain/tags/links
   EOF
   ```

2. Run: `/wiki lint`

3. Verify:
   - Lint detects missing fields
   - Lists bad-page.md with specific issues
   - LLM can fix issues based on lint output

4. Fix the page and re-lint:
   - Should have no errors for that page

## Test 6: Git Integration

**Goal**: Verify git history preservation.

1. Initialize git in vault:
   ```bash
   cd $VAULT
   git init
   git config user.name "Test User"
   git config user.email "test@example.com"
   git add .
   git commit -m "Initial vault setup"
   ```

2. Ingest a source via `/wiki ingest single`

3. Verify git log:
   ```bash
   cd $VAULT
   git log --oneline
   ```
   Should show:
   - Initial commit
   - Page creation
   - Index update (if separate commit)
   - Any log.md update

## Test 7: Guard Hook

**Goal**: Verify destructive operation blocking.

1. In Claude Code terminal, try:
   ```bash
   rm -rf $VAULT/wiki/*
   ```
   Should be **BLOCKED** by guard hook.

2. Verify guard hook message appears

3. Verify vault is unharmed:
   ```bash
   ls $VAULT/wiki/
   ```
   Should still have pages.

## Test 8: Config Update

**Goal**: Verify config modification.

1. Run: `./setup.sh` again in same vault

2. Change sources path to `raw-sources` instead of `source`

3. Verify:
   - New directories created
   - Config updated
   - Old sources still accessible (or migrated)

## Test 9: Full Workflow

**Goal**: End-to-end realistic workflow.

1. Create 3 realistic sources (articles, papers, etc.)
2. Ingest them one at a time using `/wiki ingest single`
3. Query the wiki for topics
4. Review lint findings
5. Fix any schema issues
6. Commit to git (if initialized)
7. Verify all operations in log.md

## Test 10: Error Handling

**Goal**: Verify graceful error handling.

1. Delete config file and run `/wiki ingest` → should error with helpful message
2. Create malformed JSON in config → should error gracefully
3. Run `loppy next` on vault with no sources → should return empty list
4. Create page with broken link and run `/wiki lint` → should report broken link

## Success Criteria

- [x] All 10 tests pass
- [x] No crashes or unhandled errors
- [x] Guard hook blocks destructive ops
- [x] Pages created with valid frontmatter
- [x] Index and log updated correctly
- [x] Git history preserved
- [x] Helpful error messages for failures

## Troubleshooting

**Config not found**: Run `./setup.sh` to initialize

**Sources not showing**: Verify `source/` directory exists and contains .md files

**Pages not created**: Check for schema validation errors; run `/wiki lint` to see issues

**Guard hook blocking safe commands**: Check that command isn't a regex match for destructive patterns

## Notes

- All timestamps in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Wiki pages use relative paths from wiki_dir
- Links format: `[text](wiki/category/page-name.md)`
- Index.md uses TSV format: `path | title | type | domain | updated`
