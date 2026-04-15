"""Global process state isolation tests for kanon_cli.repo.

These tests assert that calling into the repo package from Python code leaves
the calling process in the same state it was in before the call. The contract
is: sys.argv, os.execv, sys.path, os.getcwd(), and os.environ must all be
unchanged (or restored) after any API entry point into the repo package.

All tests in this module are in the TDD RED phase. They fail because
``run_from_args`` does not exist yet in ``kanon_cli.repo``. Once E0-F2-S1-T2
implements the isolation layer, these tests must all pass.
"""

import copy
import os
import sys
from typing import NoReturn

import pytest

import kanon_cli.repo as repo_pkg

_SENTINEL_REPO_DIR = "/nonexistent/.repo"
_SENTINEL_ARGS = ["version"]


def _invoke_api() -> None:
    """Invoke the repo API with sentinel arguments.

    Uses a nonexistent repo dir so the call exercises the isolation layer
    without requiring a real git repository on disk. Expected to raise
    SystemExit once run_from_args is implemented (E0-F2-S1-T2).
    """
    repo_pkg.run_from_args(_SENTINEL_ARGS, repo_dir=_SENTINEL_REPO_DIR)


@pytest.mark.unit
def test_sys_argv_unchanged_after_api_call() -> None:
    """AC-TEST-001: sys.argv must not be mutated by a repo API call.

    Snapshot sys.argv before calling run_from_args, then assert the list
    contents are identical after the call returns.
    """
    argv_before = list(sys.argv)
    with pytest.raises(SystemExit):
        _invoke_api()
    argv_after = list(sys.argv)
    assert argv_after == argv_before, (
        f"sys.argv was mutated by repo API call.\n  Before: {argv_before!r}\n  After:  {argv_after!r}"
    )


@pytest.mark.unit
def test_os_execv_never_called_during_api_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-TEST-002: os.execv must never be invoked during a repo API call.

    Monkeypatch os.execv with a sentinel that raises AssertionError if called.
    Any invocation of os.execv during run_from_args means the caller's process
    would be replaced -- a critical isolation violation.
    """
    execv_calls: list[tuple[str, list[str]]] = []

    def _record_execv(path: str, argv: list[str]) -> NoReturn:
        execv_calls.append((path, list(argv)))
        raise AssertionError(f"os.execv was called during repo API call: path={path!r}, argv={argv!r}")

    monkeypatch.setattr(os, "execv", _record_execv)
    with pytest.raises(SystemExit):
        _invoke_api()
    assert execv_calls == [], f"os.execv was called {len(execv_calls)} time(s) during repo API call: {execv_calls!r}"


@pytest.mark.unit
def test_sys_path_unchanged_after_api_call() -> None:
    """AC-TEST-003: sys.path must not be mutated by a repo API call.

    Snapshot the list contents before, compare after. The repo tool must not
    insert, remove, or reorder entries in the interpreter path.
    """
    path_before = list(sys.path)
    with pytest.raises(SystemExit):
        _invoke_api()
    path_after = list(sys.path)
    assert path_after == path_before, (
        f"sys.path was mutated by repo API call.\n  Before: {path_before!r}\n  After:  {path_after!r}"
    )


@pytest.mark.unit
def test_cwd_unchanged_after_api_call() -> None:
    """AC-TEST-004: The current working directory must not be changed by a repo API call.

    Record os.getcwd() before and after run_from_args and assert they are equal.
    """
    cwd_before = os.getcwd()
    with pytest.raises(SystemExit):
        _invoke_api()
    cwd_after = os.getcwd()
    assert cwd_after == cwd_before, (
        f"os.getcwd() changed during repo API call.\n  Before: {cwd_before!r}\n  After:  {cwd_after!r}"
    )


@pytest.mark.unit
def test_os_environ_restored_after_api_call() -> None:
    """AC-TEST-005: os.environ must be restored to its original state after a repo API call.

    Deep-copy the environment mapping before the call and compare after. Any
    key added, removed, or changed by the repo package is an isolation
    violation.
    """
    env_before = copy.deepcopy(dict(os.environ))
    with pytest.raises(SystemExit):
        _invoke_api()
    env_after = dict(os.environ)

    added = {k: env_after[k] for k in env_after if k not in env_before}
    removed = {k: env_before[k] for k in env_before if k not in env_after}
    changed = {k: (env_before[k], env_after[k]) for k in env_before if k in env_after and env_before[k] != env_after[k]}

    violations: list[str] = []
    if added:
        violations.append(f"Keys added to os.environ: {added!r}")
    if removed:
        violations.append(f"Keys removed from os.environ: {removed!r}")
    if changed:
        violations.append(f"Keys changed in os.environ: {changed!r}")

    assert not violations, "os.environ was mutated by repo API call:\n" + "\n".join(f"  {v}" for v in violations)
