# kanon

Versioned package distribution + marketplace plugin system for Claude Code configurations.

## Common Commands
- Install/sync: `uv sync`
- Tests: `uv run pytest -q`
- Lint: `uv run ruff check src tests`
- Format: `uv run ruff format src tests`
- CLI help: `uv run kanon --help`

## Repo Notes
- Main CLI entrypoint: `src/kanon_cli/__main__.py`
- Package registry and manifest logic are the core domain — changes ripple to token_miser (publishing) and loadout (consumption)
- Test markers: `@pytest.mark.unit` (fast, isolated), `@pytest.mark.functional` (CLI via subprocess)

## Working Rules

### Code quality
- Fail fast with clear errors; no fallback logic, no silent failures, no hardcoded config values
- Never make speculative claims about performance without measurement data — use qualitative descriptions ("can improve") not quantified guesses ("30% faster")
- When replacing old functionality: find all references, update all consumers, delete old code, verify zero orphaned refs — all in one commit
- Real tests only — no stubs, no mocks of the thing under test, no tests that pass by construction

### Git
- Selective `git add` — never `git add .` or `git add -A`
- Never bypass hooks, linters, or security checks (no `--no-verify`, no `# noqa` without justification)

### Security
- No credentials, tokens, or secrets in code or git — environment variables only
- Validate and sanitize all external input at system boundaries
- Pin dependencies; review security advisories before upgrading

### Documentation
- Update docs in the same commit as code changes — outdated docs are worse than no docs
- Don't create summary/overview/design documents unless explicitly requested

### Critical files (require careful review)
- Dependency manifests and lock files
- CI/CD workflows (`.github/workflows/`)
- Application config files (`*.toml`, `*.yml`)
