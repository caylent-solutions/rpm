# RPM -- Make Task Runner

Getting started with RPM using Make as your task runner. The generated Makefile wraps the RPM CLI and auto-includes targets from synced packages.

---

## Prerequisites

- GNU Make (`make --version`)
- Git

The RPM CLI is already installed (it just ran `rpm bootstrap` to create this file).

---

## Setup

### 1. Edit `.rpmenv`

Replace all `<PLACEHOLDER>` values with your project's configuration. See the `.rpmenv` Variable Reference section below for details on each variable.

### 2. Configure (sync all packages)

```bash
make rpmConfigure
```

This delegates to `rpm configure .rpmenv`, which syncs all packages to `.packages/` and updates `.gitignore`.

### 3. Verify

```bash
make help
```

After configure, `make help` shows both the RPM targets (`rpmConfigure`, `rpmClean`) and any targets contributed by synced build packages.

---

## Usage

**Configure (sync packages):**

```bash
make rpmConfigure
```

**Clean (full teardown):**

```bash
make rpmClean
```

**Or use the RPM CLI directly:**

```bash
rpm configure .rpmenv
rpm clean .rpmenv
```

---

## `.rpmenv` Variable Reference

### Core Variables

| Variable | Required | Purpose |
|---|---|---|
| `RPM_CLI_URL` | No | Git URL of the RPM CLI repository. Informational -- records which CLI version the project uses. |
| `RPM_CLI_REV` | No | Git revision (tag or branch) of the RPM CLI. Informational -- records which CLI version the project uses. |
| `REPO_URL` | Yes | Git URL of the [rpm-git-repo](https://github.com/caylent-solutions/rpm-git-repo) tool. Must be `https://github.com/caylent-solutions/rpm-git-repo.git` -- no other repo tool or fork is supported. Used by `rpm configure` to install the repo tool via pipx. |
| `REPO_REV` | Yes | rpm-git-repo version. Currently use `feat/initial-rpm-git-repo` (the only available branch). Once published to PyPI, use a tagged release or PEP 440 specifier (e.g., `~=2.0.0`, `>=2.0.0,<3.0.0`, `*`). |
| `GITBASE` | Yes | Base Git URL for your organization (e.g., `https://github.com/your-org/`). Used by `repo envsubst` to resolve `${GITBASE}` placeholders in manifest XML files. |
| `CLAUDE_MARKETPLACES_DIR` | Conditional | Directory for marketplace plugin symlinks. Required when `RPM_MARKETPLACE_INSTALL=true`. Typically `${HOME}/.claude-marketplaces`. |
| `RPM_MARKETPLACE_INSTALL` | No | Set to `true` to enable the marketplace plugin install/uninstall lifecycle during configure and clean. Default: `false`. When `false`, marketplace-related operations are skipped entirely. |

### Source Variables

Sources are auto-discovered from `RPM_SOURCE_<name>_URL` patterns and processed in alphabetical order by name. Each source requires three variables:

| Variable | Required | Purpose |
|---|---|---|
| `RPM_SOURCE_<name>_URL` | Yes | Git URL of the manifest repository for this source. |
| `RPM_SOURCE_<name>_REVISION` | Yes | Branch, tag, or PEP 440 constraint to track for this source's manifest repository. |
| `RPM_SOURCE_<name>_PATH` | Yes | Path to the entry-point manifest XML file within the manifest repository (e.g., `repo-specs/build/meta.xml`). |

You can define multiple sources. Uncomment the `marketplaces` or `tools` blocks in `.rpmenv` or add your own.

---

## How It Works

The `Makefile` reads `.rpmenv` for configuration and auto-includes all `Makefile` files from synced packages in `.packages/`. After configure, running `make help` shows both the RPM targets and any targets contributed by synced packages.

**Committed files:** `.rpmenv`, `Makefile`, `rpm-readme.md`

**Ephemeral files (gitignored):** `.packages/`, `.rpm/`

---

## Adding Sources

Uncomment or add source blocks in `.rpmenv`:

```properties
RPM_SOURCE_tools_URL=https://github.com/your-org/tools-manifests.git
RPM_SOURCE_tools_REVISION=main
RPM_SOURCE_tools_PATH=repo-specs/tools/meta.xml
```

---

## Marketplace Plugins (Optional)

To enable Claude Code marketplace plugins, set in `.rpmenv`:

```properties
RPM_MARKETPLACE_INSTALL=true
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces
```

Then add a marketplace source and re-run `make rpmConfigure`. When `RPM_MARKETPLACE_INSTALL` is `false` (the default), the marketplace lifecycle is skipped entirely -- no plugins are installed or uninstalled.

---

## Troubleshooting

- **`make rpmConfigure` fails with "rpm: command not found"** -- Reinstall the RPM CLI: `pipx install rpm-cli`
- **`make rpmConfigure` fails with ".rpmenv not found"** -- Ensure `.rpmenv` exists in the project root
- **`make help` shows no package targets** -- Run `make rpmConfigure` first to sync packages
- **Package targets not appearing after configure** -- Check that packages contain `Makefile` files with `## comment` annotations for `make help` discovery
