"""Package for the embedded repo tool.

Public API
----------
EMBEDDED
    Boolean flag that is True while run_from_args() is executing, and False
    at all other times. When True, pager.py skips os.execvp() so the calling
    process is not replaced by the pager, and forall.py saves and restores
    signal handlers around command execution.

run_from_args(argv, *, repo_dir)
    Run a repo subcommand from Python code without persistently modifying
    global process state (sys.argv, os.execv, os.environ). The function
    temporarily replaces os.execv and may temporarily write to os.environ
    during execution, but restores both in a finally block. See
    main.run_from_args for the full contract.

RepoCommandError
    Exception raised when the underlying repo command exits with an error.
    Carries the integer exit_code from the original SystemExit.
"""

from kanon_cli.repo.main import RepoCommandError
from kanon_cli.repo.main import run_from_args
from kanon_cli.repo import pager as _pager_mod

# EMBEDDED is the canonical package-level view of the embedded mode flag.
# It mirrors pager.EMBEDDED so callers can inspect it as kanon_cli.repo.EMBEDDED.
# run_from_args() writes pager.EMBEDDED directly; this property-like alias is
# implemented as a module attribute backed by the pager module's flag.


def __getattr__(name: str) -> object:
    if name == "EMBEDDED":
        return _pager_mod.EMBEDDED
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["EMBEDDED", "RepoCommandError", "run_from_args"]
