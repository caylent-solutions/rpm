"""Bootstrap business logic for scaffolding new RPM projects.

Provides functions to list available task runner templates and copy
them into a target directory with a generated ``.rpmenv`` configuration
file containing placeholder values.
"""

import pathlib
import shutil
import sys


def list_runners(catalog_dir: pathlib.Path) -> list[str]:
    """List available task runner templates from the catalog.

    Args:
        catalog_dir: Path to the catalog directory.

    Returns:
        Sorted list of runner names (catalog subdirectory names).
    """
    return sorted(d.name for d in catalog_dir.iterdir() if d.is_dir())


def bootstrap_runner(runner: str, output_dir: pathlib.Path, catalog_dir: pathlib.Path) -> None:
    """Copy runner template files and generate .rpmenv in the output directory.

    Copies all files from the catalog runner directory and generates
    a ``.rpmenv`` file with placeholder values. Refuses to overwrite
    existing files.

    Args:
        runner: Name of the runner template (e.g. ``make``, ``gradle``).
        output_dir: Target directory for the bootstrapped files.
        catalog_dir: Path to the catalog directory.

    Raises:
        SystemExit: If the runner is unknown, files already exist, or
            the output directory cannot be created.
    """
    runner_dir = catalog_dir / runner

    if not runner_dir.is_dir():
        available = list_runners(catalog_dir)
        print(
            f"Error: Unknown runner '{runner}'. Available runners: {', '.join(available)}",
            file=sys.stderr,
        )
        sys.exit(1)

    runner_files = [f.name for f in runner_dir.iterdir() if f.is_file()]
    all_files = runner_files + [".rpmenv"]

    _check_no_conflicts(all_files, output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    for src_file in runner_dir.iterdir():
        if src_file.is_file():
            shutil.copy2(src_file, output_dir / src_file.name)

    rpmenv_content = _generate_rpmenv_template()
    (output_dir / ".rpmenv").write_text(rpmenv_content)

    _print_next_steps(runner, output_dir, all_files)


def _check_no_conflicts(files: list[str], output_dir: pathlib.Path) -> None:
    """Verify no target files already exist in the output directory.

    Args:
        files: List of filenames to check.
        output_dir: Target directory.

    Raises:
        SystemExit: If any file already exists, listing all conflicts.
    """
    conflicts = [f for f in files if (output_dir / f).exists()]
    if conflicts:
        print("Error: The following files already exist:", file=sys.stderr)
        for f in conflicts:
            print(f"  {output_dir / f}", file=sys.stderr)
        print(
            "\nRemove them first or use a different --output-dir.",
            file=sys.stderr,
        )
        sys.exit(1)


def _generate_rpmenv_template() -> str:
    """Generate a .rpmenv template with placeholder values.

    Returns:
        The .rpmenv file content as a string.
    """
    return """\
# RPM Configuration
# Environment variables override these values (for pipeline integration)

# RPM CLI (install via: pipx install "git+<RPM_CLI_URL>@<RPM_CLI_REV>")
RPM_CLI_URL=<RPM_CLI_URL>
RPM_CLI_REV=<RPM_CLI_REV>

# Repo Tool (fork with envsubst support)
REPO_URL=<REPO_URL>
REPO_REV=<REPO_REV>

# Shared env vars for envsubst (resolved by 'repo envsubst' in remote.xml)
GITBASE=<GITBASE>
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces

# Marketplace install toggle
RPM_MARKETPLACE_INSTALL=false

# Source: build — build tooling packages
RPM_SOURCE_build_URL=<SOURCE_URL>
RPM_SOURCE_build_REVISION=<SOURCE_REVISION>
RPM_SOURCE_build_PATH=<SOURCE_MANIFEST_PATH>

# Uncomment to add a second source for Claude marketplace plugins:
# RPM_SOURCE_marketplaces_URL=<SOURCE_URL>
# RPM_SOURCE_marketplaces_REVISION=<SOURCE_REVISION>
# RPM_SOURCE_marketplaces_PATH=<SOURCE_MANIFEST_PATH>

# Uncomment to add additional package sources:
# RPM_SOURCE_tools_URL=<SOURCE_URL>
# RPM_SOURCE_tools_REVISION=<SOURCE_REVISION>
# RPM_SOURCE_tools_PATH=<SOURCE_MANIFEST_PATH>
"""


def _print_next_steps(
    runner: str,
    output_dir: pathlib.Path,
    files: list[str],
) -> None:
    """Print post-bootstrap instructions.

    Args:
        runner: Runner template name.
        output_dir: Directory where files were created.
        files: List of created filenames.
    """
    print(f"rpm bootstrap: created {runner} project in {output_dir}/")
    print("\nFiles created:")
    for f in sorted(files):
        print(f"  {output_dir / f}")

    print("\nNext steps:")
    print("  1. Edit .rpmenv and replace all <PLACEHOLDER> values")

    if runner == "make":
        print("  2. Run: make rpmConfigure")
    elif runner == "gradle":
        print("  2. Run: ./gradlew rpmConfigure")
    else:
        print("  2. Run: rpm configure .rpmenv")

    print("  3. Commit .rpmenv and the task runner files to your repository")
