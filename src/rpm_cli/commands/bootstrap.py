"""Bootstrap subcommand: scaffold a new RPM project.

Copies catalog entry package files from the catalog and provides
a pre-configured ``.rpmenv`` configuration file. Supports remote
catalog sources via ``--catalog-source`` flag or
``RPM_CATALOG_SOURCE`` environment variable.
"""

import argparse
import pathlib

from rpm_cli.core.bootstrap import bootstrap_package, list_packages
from rpm_cli.core.catalog import resolve_catalog_dir


def register(subparsers) -> None:
    """Register the bootstrap subcommand.

    Args:
        subparsers: The subparsers object from the parent parser.
    """
    parser = subparsers.add_parser(
        "bootstrap",
        help="Scaffold a new RPM project with catalog entry package files",
        description=(
            "Copy catalog entry package files (including a pre-configured\n"
            ".rpmenv) into the target directory.\n\n"
            "Use 'rpm bootstrap list' to see available packages."
        ),
        epilog="Examples:\n  rpm bootstrap list\n  rpm bootstrap make\n  rpm bootstrap gradle --output-dir my-project\n  rpm bootstrap rpm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "package",
        help="Catalog entry package name (e.g. make, gradle, rpm) or 'list' to show available packages",
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
        args: Parsed arguments with package, output_dir, and catalog_source.
    """
    catalog_dir = resolve_catalog_dir(args.catalog_source)

    if args.package == "list":
        packages = list_packages(catalog_dir)
        print("Available packages:")
        for pkg in packages:
            print(f"  {pkg}")
        return

    bootstrap_package(args.package, args.output_dir, catalog_dir)
