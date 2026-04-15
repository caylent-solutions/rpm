"""Comprehensive file inventory tests for the migrated repo package.

Verifies the complete file inventory of src/kanon_cli/repo/ against the
known inventory from the migration specification. This test serves as a
gate to confirm Sprint 1 copy tasks (T2, T3, T4) are fully complete before
Sprint 2 import fixes begin.

AC-FUNC-001: 25 root .py files excluding __init__.py
AC-FUNC-002: 28 .py files in subcmds/ including __init__.py
AC-FUNC-003: 53 total .py files across both directories
AC-FUNC-004: Non-Python runtime files present
AC-FUNC-005: Documentation files present under docs/
AC-FUNC-006: Inventory matches known file list from spec
AC-TEST-001: test_file_inventory_complete verifies exact expected file counts
AC-TEST-002: test_no_unexpected_files verifies no extra files were introduced
"""

import pathlib

import pytest

from tests.unit.repo.conftest import TARGET_DIR

SUBCMDS_DIR = TARGET_DIR / "subcmds"

# The 25 root Python files (excluding __init__.py) per AC-FUNC-001.
# Source: SPEC-repo-to-kanon-migration.md, section 2.1
ROOT_PYTHON_FILES = [
    "color.py",
    "command.py",
    "editor.py",
    "error.py",
    "event_log.py",
    "fetch.py",
    "git_command.py",
    "git_config.py",
    "git_refs.py",
    "git_superproject.py",
    "git_trace2_event_log.py",
    "git_trace2_event_log_base.py",
    "hooks.py",
    "main.py",
    "manifest_xml.py",
    "pager.py",
    "platform_utils.py",
    "platform_utils_win32.py",
    "progress.py",
    "project.py",
    "repo_logging.py",
    "repo_trace.py",
    "ssh.py",
    "version_constraints.py",
    "wrapper.py",
]

# The 28 subcmd Python files including __init__.py per AC-FUNC-002.
# Source: SPEC-repo-to-kanon-migration.md, section 2.1
SUBCMD_PYTHON_FILES = [
    "__init__.py",
    "abandon.py",
    "branches.py",
    "checkout.py",
    "cherry_pick.py",
    "diff.py",
    "diffmanifests.py",
    "download.py",
    "envsubst.py",
    "forall.py",
    "gc.py",
    "grep.py",
    "help.py",
    "info.py",
    "init.py",
    "list.py",
    "manifest.py",
    "overview.py",
    "prune.py",
    "rebase.py",
    "selfupdate.py",
    "smartsync.py",
    "stage.py",
    "start.py",
    "status.py",
    "sync.py",
    "upload.py",
    "version.py",
]

# Non-Python runtime files per AC-FUNC-004.
# Source: SPEC-repo-to-kanon-migration.md, section 2.1, Non-Python files table
NON_PYTHON_RUNTIME_FILES = [
    "repo",
    "git_ssh",
    "hooks/commit-msg",
    "hooks/pre-auto-gc",
    "requirements.json",
]

# Documentation files per AC-FUNC-005.
# Source: SPEC-repo-to-kanon-migration.md, section 2.1, Non-Python files table
DOCS_FILES = [
    "docs/manifest-format.md",
    "docs/internal-fs-layout.md",
    "docs/python-support.md",
    "docs/repo-hooks.md",
    "docs/smart-sync.md",
    "docs/windows.md",
    "docs/integration-testing.md",
]

# Expected total count constants.
EXPECTED_ROOT_PY_COUNT = 25
EXPECTED_SUBCMD_PY_COUNT = 28
EXPECTED_TOTAL_PY_COUNT = 53


def _collect_py_files_in_dir(directory: pathlib.Path) -> list[str]:
    """Return sorted list of .py filenames directly in directory (non-recursive).

    Args:
        directory: Directory to scan for .py files.

    Returns:
        Sorted list of filenames (not full paths) for all .py files in the directory.

    Raises:
        AssertionError: If the directory does not exist.
    """
    assert directory.is_dir(), f"Directory {directory} does not exist."
    return sorted(p.name for p in directory.iterdir() if p.is_file() and p.suffix == ".py")


# ---------------------------------------------------------------------------
# AC-TEST-001: test_file_inventory_complete
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_file_inventory_complete_root_count() -> None:
    """Verify exactly 25 root .py files exist under src/kanon_cli/repo/ (excluding __init__.py).

    AC-FUNC-001: 25 root .py files (excluding __init__.py).
    """
    actual_files = _collect_py_files_in_dir(TARGET_DIR)
    # Exclude __init__.py from the root count per AC-FUNC-001.
    non_init_files = [f for f in actual_files if f != "__init__.py"]
    assert len(non_init_files) == EXPECTED_ROOT_PY_COUNT, (
        f"Expected exactly {EXPECTED_ROOT_PY_COUNT} root .py files (excluding __init__.py) "
        f"under {TARGET_DIR}, but found {len(non_init_files)}: {non_init_files!r}. "
        f"Ensure all 25 root Python files from E0-F1-S1-T2 were copied to src/kanon_cli/repo/."
    )


@pytest.mark.unit
def test_file_inventory_complete_subcmd_count() -> None:
    """Verify exactly 28 .py files exist under src/kanon_cli/repo/subcmds/ (including __init__.py).

    AC-FUNC-002: 28 subcmd .py files including __init__.py.
    """
    actual_files = _collect_py_files_in_dir(SUBCMDS_DIR)
    assert len(actual_files) == EXPECTED_SUBCMD_PY_COUNT, (
        f"Expected exactly {EXPECTED_SUBCMD_PY_COUNT} .py files (including __init__.py) "
        f"under {SUBCMDS_DIR}, but found {len(actual_files)}: {actual_files!r}. "
        f"Ensure all 28 subcmd Python files from E0-F1-S1-T3 were copied to src/kanon_cli/repo/subcmds/."
    )


@pytest.mark.unit
def test_file_inventory_complete_total_count() -> None:
    """Verify 53 total .py files across root (25 + __init__.py) and subcmds (28).

    AC-FUNC-003: 53 total .py files (25 root + 28 subcmds).
    Note: __init__.py in root is counted here; 26 root files + 28 subcmd files = 54 total,
    but the spec defines 53 as (25 non-init root) + (28 subcmds including their __init__.py).
    We count: root non-init (25) + subcmds all (28) = 53.
    """
    root_non_init = [f for f in _collect_py_files_in_dir(TARGET_DIR) if f != "__init__.py"]
    subcmd_all = _collect_py_files_in_dir(SUBCMDS_DIR)
    total = len(root_non_init) + len(subcmd_all)
    assert total == EXPECTED_TOTAL_PY_COUNT, (
        f"Expected {EXPECTED_TOTAL_PY_COUNT} total .py files (25 root + 28 subcmds), "
        f"but found {total} ({len(root_non_init)} root non-init + {len(subcmd_all)} subcmds). "
        f"Ensure E0-F1-S1-T2 and E0-F1-S1-T3 completed successfully."
    )


@pytest.mark.unit
@pytest.mark.parametrize("filename", ROOT_PYTHON_FILES)
def test_file_inventory_complete_root_files_present(filename: str) -> None:
    """Verify each of the 25 expected root .py files exists under src/kanon_cli/repo/.

    AC-FUNC-006: Inventory matches known file list from spec.
    """
    target = TARGET_DIR / filename
    assert target.is_file(), (
        f"Expected root file {target} to exist but it is missing. "
        f"Copy {filename} from rpm-git-repo/ to src/kanon_cli/repo/ (E0-F1-S1-T2)."
    )


@pytest.mark.unit
@pytest.mark.parametrize("filename", SUBCMD_PYTHON_FILES)
def test_file_inventory_complete_subcmd_files_present(filename: str) -> None:
    """Verify each of the 28 expected subcmd .py files exists under src/kanon_cli/repo/subcmds/.

    AC-FUNC-006: Inventory matches known file list from spec.
    """
    target = SUBCMDS_DIR / filename
    assert target.is_file(), (
        f"Expected subcmd file {target} to exist but it is missing. "
        f"Copy {filename} from rpm-git-repo/subcmds/ to src/kanon_cli/repo/subcmds/ (E0-F1-S1-T3)."
    )


@pytest.mark.unit
@pytest.mark.parametrize("relative_path", NON_PYTHON_RUNTIME_FILES)
def test_file_inventory_complete_non_python_files_present(relative_path: str) -> None:
    """Verify each non-Python runtime file exists under src/kanon_cli/repo/.

    AC-FUNC-004: Non-Python runtime files (repo, git_ssh, hooks/commit-msg,
    hooks/pre-auto-gc, requirements.json) are present.
    """
    target = TARGET_DIR / relative_path
    assert target.is_file(), (
        f"Expected non-Python runtime file {target} to exist but it is missing. "
        f"Copy {relative_path} from rpm-git-repo/ to src/kanon_cli/repo/ (E0-F1-S1-T4)."
    )


@pytest.mark.unit
@pytest.mark.parametrize("relative_path", DOCS_FILES)
def test_file_inventory_complete_docs_files_present(relative_path: str) -> None:
    """Verify each documentation file exists under src/kanon_cli/repo/docs/.

    AC-FUNC-005: Documentation files exist under docs/ including manifest-format.md.
    """
    target = TARGET_DIR / relative_path
    assert target.is_file(), (
        f"Expected documentation file {target} to exist but it is missing. "
        f"Copy {relative_path} from rpm-git-repo/ to src/kanon_cli/repo/ (E0-F1-S1-T4)."
    )


# ---------------------------------------------------------------------------
# AC-TEST-002: test_no_unexpected_files
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_no_unexpected_root_python_files() -> None:
    """Verify no extra .py files were introduced in src/kanon_cli/repo/ beyond the spec inventory.

    AC-TEST-002: No extra root .py files beyond __init__.py plus the known 25.
    """
    actual_files = set(_collect_py_files_in_dir(TARGET_DIR))
    expected_files = set(ROOT_PYTHON_FILES) | {"__init__.py"}
    unexpected = actual_files - expected_files
    assert not unexpected, (
        f"Found unexpected .py files in {TARGET_DIR}: {sorted(unexpected)!r}. "
        f"Only the 25 spec-defined root files plus __init__.py are expected. "
        f"Remove or relocate any files not listed in SPEC-repo-to-kanon-migration.md."
    )


@pytest.mark.unit
def test_no_unexpected_subcmd_python_files() -> None:
    """Verify no extra .py files were introduced in src/kanon_cli/repo/subcmds/ beyond the spec inventory.

    AC-TEST-002: No extra subcmd .py files beyond the known 28.
    """
    actual_files = set(_collect_py_files_in_dir(SUBCMDS_DIR))
    expected_files = set(SUBCMD_PYTHON_FILES)
    unexpected = actual_files - expected_files
    assert not unexpected, (
        f"Found unexpected .py files in {SUBCMDS_DIR}: {sorted(unexpected)!r}. "
        f"Only the 28 spec-defined subcmd files are expected. "
        f"Remove or relocate any files not listed in SPEC-repo-to-kanon-migration.md."
    )


@pytest.mark.unit
def test_no_unexpected_docs_files() -> None:
    """Verify no unexpected files were introduced under src/kanon_cli/repo/docs/.

    AC-TEST-002: Only the 7 spec-defined documentation files exist in docs/.
    """
    docs_dir = TARGET_DIR / "docs"
    assert docs_dir.is_dir(), f"Expected docs directory {docs_dir} to exist. Ensure E0-F1-S1-T4 completed successfully."
    actual_files = sorted(p.name for p in docs_dir.iterdir() if p.is_file())
    expected_filenames = sorted(pathlib.Path(p).name for p in DOCS_FILES)
    unexpected = set(actual_files) - set(expected_filenames)
    assert not unexpected, (
        f"Found unexpected files in {docs_dir}: {sorted(unexpected)!r}. "
        f"Only the 7 spec-defined documentation files are expected. "
        f"Remove or relocate any files not listed in SPEC-repo-to-kanon-migration.md."
    )
