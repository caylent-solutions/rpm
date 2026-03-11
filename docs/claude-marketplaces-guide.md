# Claude Code Marketplaces Guide

This guide documents the Claude Code marketplace architecture used by RPM
(Repo Package Manager) to manage, distribute, and install Claude Code
marketplace plugins.

---

## Cascading Manifest Hierarchy

The marketplace system uses a cascading hierarchy of `claude-marketplaces.xml`
manifest files. Each level in the hierarchy includes its parent via XML
`<include>` tags, forming a chain from the most specific (leaf) to the most
general (common/root):

```text
meta.xml (entry point)
  └── claude-marketplaces.xml (leaf: e.g. cli)
        └── claude-marketplaces.xml (argparse)
              └── claude-marketplaces.xml (make)
                    └── claude-marketplaces.xml (python)
                          └── claude-marketplaces.xml (development)
                                └── claude-marketplaces.xml (example)
                                      └── claude-marketplaces.xml (common/root)
```

### How It Works

Each manifest file at a given level:

1. Includes its parent via an `<include>` directive
2. Adds exactly one marketplace project entry at its own level

When the `repo` tool processes the entry-point manifest (`meta.xml`), it
recursively resolves each `<include>`, accumulating all marketplace entries
from the root up to the leaf. The result is a unified set of marketplace
projects representing the full stack for a given project type.

### Example Include Pattern

```xml
<manifest>
  <!-- Include the parent level -->
  <include name="repo-specs/common/example/claude-marketplaces.xml" />

  <!-- Add this level's marketplace project -->
  <project name="rpm-claude-marketplaces"
           path=".packages/rpm-claude-marketplaces-example-dev-lint"
           remote="caylent"
           revision="refs/tags/example/development/dev-lint/1.0.0">
    <linkfile src="common/example/development/dev-lint"
              dest="${CLAUDE_MARKETPLACES_DIR}/rpm-claude-marketplaces-example-dev-lint" />
  </project>
</manifest>
```

### Benefits

- Different project types (Python, Go, Node) share common tools (linting,
  CI/CD) while adding specialized marketplaces at their own level
- Adding a new marketplace at any level automatically propagates to all
  descendants
- No duplication of project entries across manifest files

---

## Path Flattening Algorithm

Each marketplace project in the hierarchy must have a unique `path` attribute.
The path flattening algorithm converts the hierarchical directory structure
into a flat project path with a namespace prefix.

### Naming Pattern

```text
.packages/rpm-claude-marketplaces-{hierarchy-prefix}-{marketplace-name}
```

### Flattening Examples

| Hierarchy Level | Flattened Path |
|---|---|
| CLI (leaf) | `.packages/rpm-claude-marketplaces-example-cli-agent` |
| Argparse | `.packages/rpm-claude-marketplaces-example-argparse-scaffold` |
| Make | `.packages/rpm-claude-marketplaces-example-make-utils` |
| Python | `.packages/rpm-claude-marketplaces-example-python-helpers` |
| Development | `.packages/rpm-claude-marketplaces-example-dev-lint` |
| Example | `.packages/rpm-claude-marketplaces-example-example-tools` |

### Uniqueness Validation

The validation command (`rpm validate marketplace`) checks that all
`<project path="...">` values are unique across all manifests. This prevents
path collisions when aggregating from multiple sources. If two manifests
define the same path, validation fails with a clear error identifying the
duplicate.

---

## Linkfile Symlink Chain

Linkfiles are XML elements within `<project>` tags that create symlinks from
cloned package directories to a centralized Claude Code marketplaces directory.
This allows Claude Code to discover and load marketplace plugins at runtime.

### Linkfile Structure

```xml
<project name="rpm-claude-marketplaces"
         path=".packages/rpm-claude-marketplaces-example-dev-lint"
         remote="caylent"
         revision="refs/tags/example/development/dev-lint/1.0.0">
  <linkfile src="common/example/development/dev-lint"
            dest="${CLAUDE_MARKETPLACES_DIR}/rpm-claude-marketplaces-example-dev-lint" />
</project>
```

### How Linkfiles Work

1. **Source (`src`)** — A relative path within the cloned package repository
   pointing to the marketplace plugin directory
2. **Destination (`dest`)** — Must use the `${CLAUDE_MARKETPLACES_DIR}`
   environment variable, resolved at configure time by `repo envsubst`
3. **Execution** — When `repo sync` runs, it creates a symlink from the
   destination to the source package directory
4. **Discovery** — Claude Code scans `${CLAUDE_MARKETPLACES_DIR}` to find
   all registered marketplace plugins

### Validation Rules

All linkfile `dest` attributes must start with `${CLAUDE_MARKETPLACES_DIR}/`.
The following patterns are rejected:

- Absolute paths (e.g., `/opt/marketplaces/...`)
- Relative paths (e.g., `.packages/...`)
- Bare names without the variable prefix

---

## Install and Uninstall Lifecycle

The marketplace install/uninstall lifecycle is controlled by the
`RPM_MARKETPLACE_INSTALL` flag in `.rpmenv`. When enabled, RPM manages
Claude Code marketplace plugin registration and unregistration.

### Install (rpmConfigure)

When a user runs `rpmConfigure` (e.g. `./gradlew rpmConfigure`):

1. **Parse `.rpmenv`** — Read configuration and validate required variables
2. **Prepare marketplace directory** — Create `${CLAUDE_MARKETPLACES_DIR}`
   if it does not exist; clear existing contents for a clean slate
3. **For each source in alphabetical order:**
   - Run `repo init` with the source URL, revision, and manifest path
   - Run `repo envsubst` to resolve `${CLAUDE_MARKETPLACES_DIR}` and
     `${GITBASE}` placeholders
   - Run `repo sync` to clone packages and create linkfile symlinks
4. **Aggregate symlinks** — Create symlinks in `.packages/` for each
   source's packages
5. **Collision detection** — Fail immediately if two sources produce the
   same package name
6. **Install plugins** — The RPM CLI locates the `claude` binary, discovers
   marketplace entries and plugins, registers marketplaces, and installs
   plugins via the Claude Code CLI

### Uninstall (rpmClean)

When a user runs `rpmClean` (e.g. `./gradlew rpmClean`), the order is
critical — uninstall plugins before removing files:

1. **Uninstall plugins** — The RPM CLI locates the `claude` binary, discovers
   marketplace entries and plugins, uninstalls each plugin, and removes
   marketplace registrations via the Claude Code CLI
2. **Remove marketplace directory** — Delete `${CLAUDE_MARKETPLACES_DIR}`
   to prevent stale plugin references
3. **Remove `.packages/`** — Delete all synced package directories
4. **Remove `.rpm/`** — Delete RPM state directory

### Failure Handling

- If any marketplace registration or plugin install fails, `rpmConfigure`
  aborts immediately with an actionable error message
- If any plugin uninstall or marketplace removal fails, `rpmClean` aborts
  immediately with an actionable error message
- All failures surface clear diagnostics identifying the failed step
