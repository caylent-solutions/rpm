"""Clean subcommand handler."""

import pathlib

from rpm_cli.core.clean import clean


def register(subparsers) -> None:
    """Register the clean subcommand.

    Args:
        subparsers: The subparsers object from the parent parser.
    """
    parser = subparsers.add_parser(
        "clean",
        help="Full teardown: uninstall, remove dirs",
        description=(
            "Execute the full rpmClean lifecycle.\n\n"
            "If RPM_MARKETPLACE_INSTALL=true, runs the uninstall script\n"
            "and removes the marketplace directory. Then removes .packages/\n"
            "and .rpm/ directories."
        ),
        epilog="Example:\n  rpm clean .rpmenv",
        formatter_class=__import__("argparse").RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "rpmenv_path",
        type=pathlib.Path,
        help="Path to the .rpmenv configuration file",
    )
    parser.set_defaults(func=_run)


def _run(args) -> None:
    """Execute the clean command.

    Args:
        args: Parsed arguments with rpmenv_path.
    """
    clean(args.rpmenv_path)
