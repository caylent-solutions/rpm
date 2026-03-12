# Setup Guide

Step-by-step instructions for setting up RPM in new and existing projects.

## Prerequisites

- Git
- Bash shell
- Python 3 (`command -v python3`)
- Internet access (to install the repo tool and clone packages)

**For all projects:** The `rpm` CLI tool must be installed first:

```bash
pipx install "git+https://github.com/caylent-solutions/rpm.git@0.1.0"
```

The `rpm` CLI installs the repo tool automatically during `rpm configure`. Both Gradle and Make bootstraps delegate to this CLI. See the [RPM README](../README.md) for full CLI documentation.

## New Project Setup

### 1. Bootstrap Your Project

Use `rpm bootstrap` to generate the task runner files and `.rpmenv` configuration:

**For Gradle projects:**

```bash
rpm bootstrap gradle
```

**For Make projects:**

```bash
rpm bootstrap make
```

**For projects without a task runner:**

```bash
rpm bootstrap rpm
```

This creates the task runner files (if applicable) and a `.rpmenv` with placeholder values. The `rpm` runner generates only `.rpmenv` for users who want to invoke the RPM CLI directly without a task runner wrapper. Use `--output-dir` to specify a different target directory. Use `--catalog-source '<git_url>@<ref>'` or the `RPM_CATALOG_SOURCE` environment variable to fetch templates from a remote catalog repo (ref can be a branch, tag, or `latest` which resolves to the highest semver tag).

### 2. Customize `.rpmenv`

Edit `.rpmenv` and replace all `<PLACEHOLDER>` values with your project's
configuration. Set `GITBASE` to the GitHub organization hosting the packages
and configure your sources. See the
[.rpmenv variable reference](../README.md#rpmenv-variable-reference) for
the full list of supported variables.

All `.rpmenv` values can be overridden by environment variables of the same name
(useful for CI/CD pipelines).

### 3. Customize `build.gradle` (Gradle only)

Replace the template's project-specific section with your own. RPM provides
plugins but does NOT manage dependency versions — each project owns its version
pins and BOM imports. See
the [RPM README](../README.md) for a detailed `build.gradle` example.

### 4. Run rpmConfigure

**Gradle:**

```bash
./gradlew rpmConfigure
```

**Make:**

```bash
make rpmConfigure
```

**CLI directly:**

```bash
rpm configure .rpmenv
```

### 5. Verify

```bash
./gradlew tasks       # Should show package-provided tasks
./gradlew build       # Should compile and run checks
```

## Existing Project Migration

For existing projects, follow the same steps above but adapt your existing build configuration to include RPM's task runner files alongside your current setup.

## Troubleshooting

### `rpmConfigure` fails with "python3 is not installed"

Python 3 must be available on PATH before running `rpmConfigure`.

- **DevContainer:** Python is provided by the devcontainer Python feature.
- **CI/CD:** Add a Python installation step before running your task runner.
- **Local:** Install Python 3 via your system package manager.

### `rpmConfigure` fails with "pipx is not installed"

pipx must be available on PATH to install the `rpm` CLI. Install it with `python3 -m pip install --user pipx && pipx ensurepath`.

### `rpmConfigure` fails with "rpm: command not found"

The `rpm` CLI must be installed before running `rpmConfigure`. Install it with `pipx install "git+https://github.com/caylent-solutions/rpm.git@0.1.0"`.

### `repo envsubst` fails

Ensure `GITBASE` is set in `.rpmenv` and is a valid URL ending with `/`.

### `repo sync` fails with authentication errors

Ensure `git` can authenticate with the Git hosting provider for your package repositories (SSH keys or credential helper).

### Package scripts are not applied (Gradle only)

Ensure `.packages/` exists and contains package directories. Run `./gradlew rpmConfigure` first.
