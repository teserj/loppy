# Loppy Plugin Release Checklist

Complete this checklist before releasing a new version of Loppy.

## Pre-Release Review

- [ ] All tests passing (run: `bats tests/**/*.bats`)
- [ ] CI workflow passing on main branch
- [ ] No TODO/FIXME comments in code
- [ ] Code review completed
- [ ] Documentation reviewed and up-to-date

## Feature Validation

- [ ] `/wiki ingest single` works end-to-end
- [ ] `/wiki ingest batch` works for multiple sources
- [ ] `/wiki query` searches wiki correctly
- [ ] `/wiki lint` validates schema accurately
- [ ] `loppy config` displays correct configuration
- [ ] `loppy next N` lists unprocessed sources
- [ ] `loppy move` relocates sources correctly
- [ ] `loppy index-merge` updates index.md atomically
- [ ] `loppy log` appends operations to log.md
- [ ] `loppy lint-frontmatter` validates all pages

## Integration Testing

- [ ] Guard hook blocks destructive operations (rm, shred, mv)
- [ ] Guard hook allows safe operations (find, grep, git mv)
- [ ] Guard hook allows non-bash tools
- [ ] Plugin loads without errors in Claude Code
- [ ] All slash commands appear in command palette

## Security

- [ ] No hardcoded credentials or secrets
- [ ] No world-writable files or directories
- [ ] Config file permissions reasonable (~/.config/loppy/config.json)
- [ ] Guard hook properly validates all vault paths
- [ ] No path traversal vulnerabilities in any subcommand

## Documentation

- [ ] CLAUDE.md covers all essential AI operation guidance
- [ ] README.md has complete setup and usage instructions
- [ ] README.md includes troubleshooting section
- [ ] E2E protocol (tests/fixtures/e2e-protocol.md) is complete
- [ ] All code examples in docs are accurate
- [ ] Karpathy inspiration clearly attributed

## Manifest and Config

- [ ] plugin.json has all required fields (name, version, description, author)
- [ ] plugin.json lists all 6 CLI commands
- [ ] plugin.json registers guard-vault hook
- [ ] plugin.json defines /wiki slash command with 3 subcommands
- [ ] Configuration schema matches implementation
- [ ] All command descriptions are clear and accurate

## Testing Coverage

- [ ] 40+ tests for bin/loppy commands
- [ ] 21+ tests for guard hook
- [ ] 10+ tests for templates
- [ ] 11+ tests for setup.sh
- [ ] 16+ tests for plugin.json
- [ ] 7+ tests for /wiki slash command
- [ ] 10+ tests for documentation
- [ ] 15+ E2E integration tests
- [ ] Manual E2E protocol at tests/fixtures/e2e-protocol.md

## Final Checks

- [ ] No merge conflicts in any files
- [ ] All commits have meaningful messages
- [ ] Git history is clean (no `git commit --amend` on shared branches)
- [ ] Branch ready for merge to main
- [ ] Version bumped in plugin.json
- [ ] CHANGELOG updated (if applicable)

## Post-Merge Tasks

- [ ] Tag release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push tags: `git push origin --tags`
- [ ] Announce release on appropriate channels
- [ ] Monitor for bug reports

## Sign-Off

- [ ] Reviewed by: ___________________
- [ ] Approved by: ___________________
- [ ] Release date: ___________________
- [ ] Version: ___________________

---

**Notes:**

Before checking off "Feature Validation" items, test each one manually using the E2E protocol or a fresh vault. Don't rely solely on automated tests.

For "Integration Testing", test in actual Claude Code environment, not just in bash.

Treat security checklist seriously; don't skip these items.

Release only when all items are checked.
