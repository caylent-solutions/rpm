"""Configure subcommand: prereqs + repo install + lifecycle.

Checks that pipx is available, resolves the repo tool version
(fuzzy if needed), installs the repo tool via pipx, then delegates
to the core configure logic.
"""

import pathlib
import shutil
import subprocess
import sys

from rpm_cli.core.configure import configure
from rpm_cli.version import resolve_version


def register(subparsers) -> None:
    """Register the configure subcommand.

    Args:
        subparsers: The subparsers object from the parent parser.
    """
    parser = subparsers.add_parser(
        "configure",
        help="Full lifecycle: check prereqs, install repo, multi-source sync",
        description=(
            "Execute the full rpmConfigure lifecycle.\n\n"
            "Checks prerequisites (pipx on PATH), installs the repo tool,\n"
            "then runs repo init/envsubst/sync for each source defined in\n"
            "the .rpmenv file. Aggregates packages into .packages/ via symlinks."
        ),
        epilog="Example:\n  rpm configure .rpmenv",
        formatter_class=__import__("argparse").RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "rpmenv_path",
        type=pathlib.Path,
        help="Path to the .rpmenv configuration file",
    )
    parser.set_defaults(func=_run)


def _run(args) -> None:
    """Execute the configure command.

    Args:
        args: Parsed arguments with rpmenv_path.
    """
    print("rpm configure: checking prerequisites...")
    _check_pipx()

    from rpm_cli.core.rpmenv import parse_rpmenv

    config = parse_rpmenv(args.rpmenv_path)
    globals_dict = config["globals"]

    repo_url = globals_dict.get("REPO_URL", "")
    repo_rev = globals_dict.get("REPO_REV", "")

    if repo_url and repo_rev:
        resolved_rev = resolve_version(repo_url, repo_rev)
        print(f"rpm configure: installing repo tool ({resolved_rev})...")
        _install_repo_tool(repo_url, resolved_rev)

    configure(args.rpmenv_path)


def _check_pipx() -> None:
    """Verify that pipx is available on PATH.

    Raises:
        SystemExit: If pipx is not found.
    """
    if shutil.which("pipx") is None:
        print(
            "Error: pipx is not installed or not on PATH.\n\n"
            "Install pipx before running rpm configure.\n"
            "  - pip: python3 -m pip install --user pipx\n"
            "  - apt: sudo apt install pipx\n"
            "  - brew: brew install pipx\n"
            "After installing: pipx ensurepath",
            file=sys.stderr,
        )
        sys.exit(1)


def _install_repo_tool(repo_url: str, repo_rev: str) -> None:
    """Install the repo tool via pipx.

    Args:
        repo_url: Git URL of the repo tool.
        repo_rev: Resolved version/branch/tag to install.

    Raises:
        SystemExit: If pipx install fails.
    """
    install_spec = f"git+{repo_url}@{repo_rev}"
    result = subprocess.run(
        ["pipx", "install", "--force", install_spec],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"Error: Failed to install repo tool via pipx: {result.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)
