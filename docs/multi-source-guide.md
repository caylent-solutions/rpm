# Multi-Source RPM Bootstrap Guide

This guide documents how RPM supports multiple manifest sources,
enabling teams to compose packages from different repositories
and organizations.

---

## Named Source Format (.rpmenv)

RPM auto-discovers sources from `RPM_SOURCE_<name>_URL` variable patterns in `.rpmenv`.
Each source is defined by a set of variables following the
`RPM_SOURCE_<name>_<property>` naming convention (`_URL`, `_REVISION`, `_PATH`).
Sources are processed in alphabetical order by name.

See the [.rpmenv variable reference](../README.md#rpmenv-variable-reference)
for the full variable table.

### Example .rpmenv Configuration

```properties
# Sources are auto-discovered from RPM_SOURCE_<name>_URL patterns.
# No explicit source list is needed — names are extracted from _URL keys
# and processed in alphabetical order (build-tools, then marketplace).

# Build tools source
RPM_SOURCE_build_tools_URL=https://github.com/org/rpm-build-tools.git
RPM_SOURCE_build_tools_REVISION=v2.0.0
RPM_SOURCE_build_tools_PATH=repo-specs/meta.xml

# Marketplace source
RPM_SOURCE_marketplace_URL=https://github.com/org/rpm-marketplace.git
RPM_SOURCE_marketplace_REVISION=main
RPM_SOURCE_marketplace_PATH=repo-specs/common/example/development/python/make/argparse/cli/meta.xml

# Global variables available to all sources
GITBASE=https://github.com/org/
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces
```

Sources are auto-discovered from `RPM_SOURCE_<name>_URL` variable patterns
and processed in alphabetical order by name. Environment variables override
`.rpmenv` file values, allowing the same configuration to work across environments.

---

## Source Isolation

Each source is initialized and synced in its own isolated directory
under `.rpm/sources/<name>/`. This prevents sources from interfering
with each other.

### Directory Structure

```text
.rpm/
└── sources/
    ├── marketplace/          # Isolated workspace for marketplace source
    │   ├── .repo/            # repo tool metadata
    │   └── .packages/        # Packages synced from this source
    │       └── rpm-claude-marketplaces-example-dev-lint/
    └── build-tools/          # Isolated workspace for build-tools source
        ├── .repo/
        └── .packages/
            └── rpm-build-conventions/
```

### Why Isolation Matters

- Each source gets its own `repo init` / `repo sync` cycle
- Sources cannot overwrite each other's `.repo/` metadata
- Failures in one source do not corrupt another source's state
- Sources can use different manifest URLs, revisions, and paths

---

## Symlink Aggregation

After all sources are synced, RPM aggregates their packages into
a single top-level `.packages/` directory using symlinks. This gives
consumers a unified view of all packages regardless of which source
provided them.

### Aggregation Process

1. For each source in alphabetical order, scan `.rpm/sources/<name>/.packages/`
2. For each package directory found, create a symlink in the top-level `.packages/`
3. The symlink points from `.packages/<pkg-name>` to `.rpm/sources/<name>/.packages/<pkg-name>`

### Result

```text
.packages/                                         # Unified view (symlinks)
├── rpm-claude-marketplaces-example-dev-lint -> .rpm/sources/marketplace/.packages/rpm-claude-marketplaces-example-dev-lint
└── rpm-build-conventions -> .rpm/sources/build-tools/.packages/rpm-build-conventions
```

Consumers reference packages from `.packages/` without needing to know
which source provided them.

---

## Collision Detection

When two sources produce a package with the same name, RPM detects the
collision and fails immediately with an actionable error message.

### How It Works

During symlink aggregation, RPM tracks which source provided each
package name. If a package name already exists from a previous source,
aggregation aborts with an error identifying both the conflicting
sources and the duplicate package name.

### Example Error

```text
Error: Package collision for 'rpm-shared-utils':
  provided by source 'marketplace' and source 'build-tools'
```

### Resolution

- Rename one of the conflicting packages in its manifest
- Remove the duplicate from one source
- Remove the `RPM_SOURCE_<name>_*` variables for the source with the unwanted duplicate

Collision detection runs after all sources are synced, ensuring that
the error is caught before any consumer code runs.
