"""Tests for wrapper version check behavior in embedded mode.

Verifies that:
- _CheckWrapperVersion() is skipped when EMBEDDED=True
- A constant version string (EMBEDDED_WRAPPER_VERSION) is available from wrapper.py
- Version.wrapper_version is set to EMBEDDED_WRAPPER_VERSION in embedded mode
- Normal CLI mode still performs the wrapper version check
"""

import pytest

import kanon_cli.repo.main as repo_main
import kanon_cli.repo.pager as repo_pager
import kanon_cli.repo.wrapper as repo_wrapper


# ---------------------------------------------------------------------------
# AC-FUNC-002 / AC-TEST-002: constant version string in embedded mode
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_embedded_wrapper_version_constant_exists() -> None:
    """AC-FUNC-002, AC-TEST-002: wrapper.py must expose EMBEDDED_WRAPPER_VERSION constant."""
    assert hasattr(repo_wrapper, "EMBEDDED_WRAPPER_VERSION"), (
        "wrapper.py must expose EMBEDDED_WRAPPER_VERSION for embedded mode"
    )


@pytest.mark.unit
def test_embedded_wrapper_version_is_non_empty_string() -> None:
    """AC-FUNC-002, AC-TEST-002: EMBEDDED_WRAPPER_VERSION must be a non-empty string."""
    version = repo_wrapper.EMBEDDED_WRAPPER_VERSION
    assert isinstance(version, str), f"EMBEDDED_WRAPPER_VERSION must be a str, got {type(version)!r}"
    assert version, "EMBEDDED_WRAPPER_VERSION must be a non-empty string"


@pytest.mark.unit
def test_embedded_wrapper_version_matches_expected_format() -> None:
    """AC-FUNC-002: EMBEDDED_WRAPPER_VERSION must be in dotted-integer format (e.g. '2.54')."""
    version = repo_wrapper.EMBEDDED_WRAPPER_VERSION
    parts = version.split(".")
    assert len(parts) >= 2, f"EMBEDDED_WRAPPER_VERSION must have at least two dotted parts, got {version!r}"
    for part in parts:
        assert part.isdigit(), (
            f"Each part of EMBEDDED_WRAPPER_VERSION must be a digit string, got part={part!r} in {version!r}"
        )


# ---------------------------------------------------------------------------
# AC-FUNC-001 / AC-TEST-001: _CheckWrapperVersion skipped when EMBEDDED=True
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_check_wrapper_version_skipped_in_embedded_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-FUNC-001, AC-TEST-001: _CheckWrapperVersion must not be called when EMBEDDED=True."""
    monkeypatch.setattr(repo_pager, "EMBEDDED", True)

    check_calls: list[tuple[str, str]] = []

    def _record_check(ver_str: str, repo_path: str) -> None:
        check_calls.append((ver_str, repo_path))

    monkeypatch.setattr(repo_main, "_CheckWrapperVersion", _record_check)

    # Patch _CheckRepoDir to do nothing so we can isolate just _CheckWrapperVersion behavior.
    monkeypatch.setattr(repo_main, "_CheckRepoDir", lambda repo_dir: None)

    # Patch _Repo to raise SystemExit(0) immediately to stop execution after startup checks.
    class _StopHere(SystemExit):
        pass

    original_repo_class = repo_main._Repo

    class _ImmediateExit(original_repo_class):
        def __init__(self, repodir: str) -> None:
            raise _StopHere(0)

    monkeypatch.setattr(repo_main, "_Repo", _ImmediateExit)

    with pytest.raises((_StopHere, SystemExit)):
        repo_main._Main(["--repo-dir=/nonexistent/.repo", "--wrapper-version=2.54", "--wrapper-path=/fake/repo", "--"])

    assert check_calls == [], (
        f"_CheckWrapperVersion was called {len(check_calls)} time(s) even though EMBEDDED=True: {check_calls!r}"
    )


@pytest.mark.unit
def test_check_wrapper_version_not_skipped_in_cli_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-FUNC-003, AC-TEST-003: _CheckWrapperVersion must be called when EMBEDDED=False (normal CLI mode)."""
    monkeypatch.setattr(repo_pager, "EMBEDDED", False)

    check_calls: list[tuple[str, str]] = []

    def _record_and_pass(ver_str: str, repo_path: str) -> None:
        check_calls.append((ver_str, repo_path))

    monkeypatch.setattr(repo_main, "_CheckWrapperVersion", _record_and_pass)
    monkeypatch.setattr(repo_main, "_CheckRepoDir", lambda repo_dir: None)

    class _StopHere(SystemExit):
        pass

    original_repo_class = repo_main._Repo

    class _ImmediateExit(original_repo_class):
        def __init__(self, repodir: str) -> None:
            raise _StopHere(0)

    monkeypatch.setattr(repo_main, "_Repo", _ImmediateExit)

    with pytest.raises((_StopHere, SystemExit)):
        repo_main._Main(["--repo-dir=/nonexistent/.repo", "--wrapper-version=2.54", "--wrapper-path=/fake/repo", "--"])

    assert len(check_calls) == 1, (
        f"_CheckWrapperVersion should be called exactly once in CLI mode, got {len(check_calls)} calls: {check_calls!r}"
    )


# ---------------------------------------------------------------------------
# AC-FUNC-004 / AC-TEST-001: no error raised in embedded mode without launcher script
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_no_error_in_embedded_mode_without_wrapper_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-FUNC-004, AC-TEST-001: No error must be raised in embedded mode even without a wrapper_version arg.

    In embedded mode, _CheckWrapperVersion would call sys.exit(1) if wrapper_version
    is empty. Skipping the check ensures embedded callers are unaffected.
    """
    monkeypatch.setattr(repo_pager, "EMBEDDED", True)
    monkeypatch.setattr(repo_main, "_CheckRepoDir", lambda repo_dir: None)

    class _StopHere(SystemExit):
        pass

    original_repo_class = repo_main._Repo

    class _ImmediateExit(original_repo_class):
        def __init__(self, repodir: str) -> None:
            raise _StopHere(0)

    monkeypatch.setattr(repo_main, "_Repo", _ImmediateExit)

    # Pass no --wrapper-version; in normal mode this triggers sys.exit(1).
    # In embedded mode it must not raise.
    try:
        repo_main._Main(["--repo-dir=/nonexistent/.repo", "--"])
    except _StopHere:
        pass  # Expected -- execution reached _Repo, which means no sys.exit(1) from version check.
    except SystemExit as exc:
        # Any sys.exit with non-zero is a failure in embedded mode.
        assert exc.code == 0, (
            f"sys.exit was called with non-zero code {exc.code!r} in embedded mode -- "
            "probably _CheckWrapperVersion ran and rejected the missing wrapper version."
        )


# ---------------------------------------------------------------------------
# AC-FUNC-002 / AC-TEST-002: run_from_args uses EMBEDDED_WRAPPER_VERSION
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_run_from_args_passes_embedded_wrapper_version_to_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-FUNC-002, AC-TEST-002: run_from_args must pass EMBEDDED_WRAPPER_VERSION as --wrapper-version.

    When running in embedded mode, run_from_args should inject the constant
    EMBEDDED_WRAPPER_VERSION into the internal argv so _Main receives a stable,
    known version string that will pass _CheckWrapperVersion (which is skipped
    anyway in embedded mode, but the version must still be set for Version.wrapper_version).
    """
    captured_argv: list[list[str]] = []

    def _capture_main(argv: list[str]) -> None:
        captured_argv.append(list(argv))
        raise SystemExit(0)

    monkeypatch.setattr(repo_main, "_Main", _capture_main)

    from kanon_cli.repo.main import run_from_args

    run_from_args(["version"], repo_dir="/nonexistent/.repo")

    assert len(captured_argv) == 1, f"_Main should be called once, got {len(captured_argv)}"
    main_argv = captured_argv[0]

    # Find the --wrapper-version argument.
    wrapper_version_args = [arg for arg in main_argv if arg.startswith("--wrapper-version=")]
    assert len(wrapper_version_args) == 1, (
        f"Expected exactly one --wrapper-version arg in internal argv, got: {wrapper_version_args!r}\n"
        f"Full argv: {main_argv!r}"
    )

    actual_version = wrapper_version_args[0].split("=", 1)[1]
    expected_version = repo_wrapper.EMBEDDED_WRAPPER_VERSION
    assert actual_version == expected_version, (
        f"run_from_args must pass EMBEDDED_WRAPPER_VERSION={expected_version!r} as --wrapper-version, "
        f"got {actual_version!r}"
    )
