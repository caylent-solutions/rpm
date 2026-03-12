"""Bootstrap subcommand: scaffold a new RPM project.

Copies task runner template files from the catalog and generates
a ``.rpmenv`` configuration file with placeholder values. Supports
remote catalog sources via ``--catalog-source`` flag or
``RPM_CATALOG_SOURCE`` environment variable.
"""

import argparse
import pathlib

from rpm_cli.core.bootstrap import bootstrap_runner, list_runners
from rpm_cli.core.catalog import resolve_catalog_dir


def register(subparsers) -> None:
    """Register the bootstrap subcommand.

    Args:
        subparsers: The subparsers object from the parent parser.
    """
    parser = subparsers.add_parser(
        "bootstrap",
        help="Scaffold a new RPM project with task runner files",
        description=(
            "Copy task runner template files and generate a .rpmenv\n"
            "configuration file with placeholder values.\n\n"
            "Use 'rpm bootstrap list' to see available runners."
        ),
        epilog="Examples:\n  rpm bootstrap list\n  rpm bootstrap make\n  rpm bootstrap gradle --output-dir my-project\n  rpm bootstrap rpm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "runner",
        help="Runner template name (e.g. make, gradle, rpm) or 'list' to show available runners",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("."),
        help="Target directory for bootstrapped files (default: current directory)",
    )
    parser.add_argument(
        "--catalog-source",
        default=None,
        help=(
            "Remote catalog source as '<git_url>@<ref>' where ref is a branch, "
            "tag, or 'latest'. Overrides RPM_CATALOG_SOURCE env var. "
            "Default: bundled catalog."
        ),
    )
    parser.set_defaults(func=_run)


def _run(args) -> None:
    """Execute the bootstrap command.

    Args:
        args: Parsed arguments with runner, output_dir, and catalog_source.
    """
    catalog_dir = resolve_catalog_dir(args.catalog_source)

    if args.runner == "list":
        runners = list_runners(catalog_dir)
        print("Available runners:")
        for runner in runners:
            print(f"  {runner}")
        return

    bootstrap_runner(args.runner, args.output_dir, catalog_dir)
