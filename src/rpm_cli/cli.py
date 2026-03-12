"""RPM CLI entry point with argparse subcommands.

Provides the top-level ``rpm`` command with subcommands:
  - ``rpm configure <rpmenv-path>`` -- Full lifecycle: prereqs + repo install + multi-source sync
  - ``rpm clean <rpmenv-path>`` -- Full teardown: uninstall, remove dirs
  - ``rpm validate xml [--repo-root PATH]`` -- Validate manifest XML files
  - ``rpm validate marketplace [--repo-root PATH]`` -- Validate marketplace XML manifests
  - ``rpm bootstrap <runner>`` -- Scaffold a new RPM project (make, gradle, or rpm)
  - ``rpm bootstrap list`` -- List available task runner templates
"""

import argparse
import sys

from rpm_cli import __version__
from rpm_cli.commands.bootstrap import register as register_bootstrap
from rpm_cli.commands.clean import register as register_clean
from rpm_cli.commands.configure import register as register_configure
from rpm_cli.commands.validate import register as register_validate


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands.

    Returns:
        The configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="rpm",
        description="RPM (Repo Package Manager) CLI tool. Manages the full RPM lifecycle: configure, clean, and validate.",
        epilog="Examples:\n  rpm configure .rpmenv\n  rpm clean .rpmenv\n  rpm validate xml\n  rpm validate marketplace --repo-root /path/to/repo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description="Available subcommands",
    )

    register_bootstrap(subparsers)
    register_configure(subparsers)
    register_clean(subparsers)
    register_validate(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate subcommand.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(2)

    args.func(args)
