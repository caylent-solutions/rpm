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

repo_envsubst(repo_dir, env_vars)
    Perform environment variable substitution in manifest XML files under
    <repo_dir>/.repo/manifests/. Temporarily injects env_vars into os.environ,
    delegates to run_from_args() with ["envsubst"], and restores os.environ
    in a finally block (even on failure). Raises RepoCommandError on failure.

RepoCommandError
    Exception raised when the underlying repo command exits with an error.
    Carries the integer exit_code from the original SystemExit.
"""

import os

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


def repo_envsubst(repo_dir: str, env_vars: dict[str, str]) -> None:
    """Perform environment variable substitution in manifest XML files.

    Substitutes ${VAR} placeholders in all XML files under
    <repo_dir>/.repo/manifests/ using the supplied env_vars dict. The
    substitution is delegated to the embedded ``repo envsubst`` subcommand.

    Fails fast if repo_dir does not contain a .repo/ subdirectory -- this
    indicates repo init has not been run in repo_dir and the envsubst command
    cannot locate any manifest XML files to process.

    The function temporarily injects env_vars into os.environ before invoking
    run_from_args() and restores os.environ to its original state in a finally
    block, so the calling process observes no persistent environment change
    regardless of whether the call succeeds or fails.

    The function also temporarily changes the working directory to repo_dir so
    that the envsubst subcommand can locate manifest XML files using relative
    paths. The original working directory is restored in a finally block.

    Args:
        repo_dir: Path to the repository root directory that contains the
            .repo/ subdirectory. Must be a directory in which ``repo init``
            has already been run.
        env_vars: Mapping of environment variable names to values to inject
            before running ``repo envsubst``. These variables are removed from
            os.environ (or restored to their pre-call values) after the call
            completes.

    Returns:
        None on success (repo envsubst exits with code 0).

    Raises:
        RepoCommandError: When repo_dir does not contain a .repo/ subdirectory,
            indicating that repo init has not been run in that directory.
        RepoCommandError: When the underlying ``repo envsubst`` command exits
            with a non-zero exit code. The exit_code attribute of the exception
            carries the integer exit code from the underlying failure.
    """
    repo_dot_dir = os.path.join(repo_dir, ".repo")
    if not os.path.isdir(repo_dot_dir):
        raise RepoCommandError(
            exit_code=1,
            message=(
                f"repo envsubst requires a repo checkout: {repo_dot_dir!r} does not exist. "
                f"Run 'repo init' in {repo_dir!r} before calling repo_envsubst()."
            ),
        )

    environ_snapshot = dict(os.environ)
    cwd_snapshot = os.getcwd()
    try:
        for key, value in env_vars.items():
            os.environ[key] = value
        os.chdir(repo_dir)
        run_from_args(["envsubst"], repo_dir=repo_dot_dir)
    finally:
        os.chdir(cwd_snapshot)
        keys_to_remove = [k for k in list(os.environ) if k not in environ_snapshot]
        for k in keys_to_remove:
            del os.environ[k]
        for k, v in environ_snapshot.items():
            if os.environ.get(k) != v:
                os.environ[k] = v


__all__ = ["EMBEDDED", "RepoCommandError", "repo_envsubst", "run_from_args"]
