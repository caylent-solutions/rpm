# Configuration (.rpmenv)

The `.rpmenv` file is a shell-compatible KEY=VALUE configuration file that drives the RPM lifecycle.

## Format

```properties
# Comments start with #
KEY=VALUE
KEY_WITH_EXPANSION=${HOME}/.some-path
```

- Lines starting with `#` are comments
- Blank lines are ignored
- Lines without `=` are ignored
- Only the first `=` splits key from value (values may contain `=`)
- Trailing whitespace is trimmed

## Shell Variable Expansion

Values can reference environment variables using `${VAR}` syntax:

```properties
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces
```

If the referenced variable is not set in the environment, parsing fails with a descriptive error.

## Environment Variable Overrides

Every `.rpmenv` variable can be overridden by an environment variable of the same name. This enables CI/CD pipelines to customize behavior without modifying the file:

```bash
REPO_REV=v3.0.0 rpm configure .rpmenv
```

## Multi-Source Groups

Sources are auto-discovered from `RPM_SOURCE_<name>_URL` variable patterns and processed in alphabetical order by name:

```properties
RPM_SOURCE_build_URL=https://github.com/org/build-repo.git
RPM_SOURCE_build_REVISION=main
RPM_SOURCE_build_PATH=repo-specs/meta.xml

RPM_SOURCE_marketplaces_URL=https://github.com/org/mp-repo.git
RPM_SOURCE_marketplaces_REVISION=main
RPM_SOURCE_marketplaces_PATH=repo-specs/marketplaces.xml
```

Each source requires `_URL`, `_REVISION`, and `_PATH` suffixed variables.

## RPM_MARKETPLACE_INSTALL Toggle

When `RPM_MARKETPLACE_INSTALL=true`:

- `rpm configure` creates and cleans `CLAUDE_MARKETPLACES_DIR`, then runs the install script post-sync
- `rpm clean` runs the uninstall script and removes `CLAUDE_MARKETPLACES_DIR`

When `false` (default), marketplace lifecycle is skipped entirely.
