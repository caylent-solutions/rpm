"""Tests verifying non-Python runtime files are copied to src/kanon_cli/repo/.

Covers:
- repo launcher script
- git_ssh helper script
- hooks/commit-msg and hooks/pre-auto-gc git hook scripts
- requirements.json manifest
- All documentation files from docs/

Executable permissions are verified for repo, git_ssh, and all hook scripts.
"""

import hashlib
import stat

import pytest

from tests.unit.repo.conftest import TARGET_DIR, get_rpm_source_dir


NON_PYTHON_RUNTIME_FILES = [
    "repo",
    "git_ssh",
    "hooks/commit-msg",
    "hooks/pre-auto-gc",
    "requirements.json",
    "docs/integration-testing.md",
    "docs/internal-fs-layout.md",
    "docs/manifest-format.md",
    "docs/python-support.md",
    "docs/repo-hooks.md",
    "docs/smart-sync.md",
    "docs/windows.md",
]


EXECUTABLE_FILES = [
    "repo",
    "git_ssh",
    "hooks/commit-msg",
    "hooks/pre-auto-gc",
]


@pytest.mark.unit
@pytest.mark.parametrize("relative_path", NON_PYTHON_RUNTIME_FILES)
def test_non_python_runtime_files_exist(relative_path: str) -> None:
    """Verify each non-Python runtime file exists under src/kanon_cli/repo/."""
    target = TARGET_DIR / relative_path
    assert target.is_file(), (
        f"Expected file {target} to exist but it does not. "
        f"Copy {relative_path} from rpm-git-repo/ to src/kanon_cli/repo/."
    )


@pytest.mark.unit
@pytest.mark.parametrize("relative_path", EXECUTABLE_FILES)
def test_executable_permissions_preserved(relative_path: str) -> None:
    """Verify executable permission (+x) is set on runtime scripts and hook files."""
    target = TARGET_DIR / relative_path
    assert target.is_file(), (
        f"Expected file {target} to exist but it does not. "
        f"Copy {relative_path} from rpm-git-repo/ to src/kanon_cli/repo/ with executable permission."
    )
    mode = target.stat().st_mode
    assert mode & stat.S_IXUSR, (
        f"File {target} is missing user-executable permission (stat.S_IXUSR). "
        f"Ensure executable permission is preserved when copying {relative_path}."
    )


@pytest.mark.unit
@pytest.mark.parametrize("relative_path", NON_PYTHON_RUNTIME_FILES)
def test_non_python_files_content_matches_source(relative_path: str) -> None:
    """Verify each copied non-Python file has content matching its source.

    The source file SHA-256 checksum is compared to the target file SHA-256
    checksum. For Markdown documentation files, em-dash characters (U+2014) are
    replaced with double-hyphen (--) before comparison so that required
    code-quality cleanup does not cause spurious mismatches.

    This test is skipped when RPM_GIT_REPO_PATH is not set.
    """
    source_dir = get_rpm_source_dir()

    if relative_path.startswith("docs/"):
        doc_filename = relative_path[len("docs/") :]
        source_file = source_dir / "docs" / doc_filename
    elif "/" in relative_path:
        # hooks/commit-msg or hooks/pre-auto-gc
        parts = relative_path.split("/", 1)
        source_file = source_dir / parts[0] / parts[1]
    else:
        source_file = source_dir / relative_path

    target_file = TARGET_DIR / relative_path

    assert source_file.is_file(), (
        f"Source file {source_file} does not exist. Verify RPM_GIT_REPO_PATH={source_dir!r} is correct."
    )
    assert target_file.is_file(), (
        f"Target file {target_file} does not exist. Copy {relative_path} from rpm-git-repo/ to src/kanon_cli/repo/."
    )

    source_bytes = _normalize_content(source_file.read_bytes(), relative_path)
    target_bytes = _normalize_content(target_file.read_bytes(), relative_path)

    source_checksum = hashlib.sha256(source_bytes).hexdigest()
    target_checksum = hashlib.sha256(target_bytes).hexdigest()

    assert source_checksum == target_checksum, (
        f"Content mismatch for {relative_path}: "
        f"source SHA256={source_checksum}, target SHA256={target_checksum}. "
        f"Ensure {relative_path} was copied without altering its logical content "
        f"(em-dash replacements in Markdown are permitted)."
    )


def _normalize_content(content: bytes, relative_path: str) -> bytes:
    """Normalize file content for comparison purposes.

    For Markdown files, em-dash characters (U+2014) are replaced with
    double-hyphen (--) so that required code-quality cleanup does not
    cause spurious content-match failures.

    Args:
        content: Raw file bytes to normalize.
        relative_path: The relative path of the file (used to detect Markdown).

    Returns:
        Normalized bytes for checksum comparison.
    """
    if relative_path.endswith(".md"):
        text = content.decode("utf-8")
        text = text.replace("\u2014", "--")
        return text.encode("utf-8")
    return content


@pytest.mark.unit
def test_gitkeep_files_removed() -> None:
    """Verify .gitkeep placeholder files are not present in hooks/ or docs/."""
    for directory in ["hooks", "docs"]:
        gitkeep = TARGET_DIR / directory / ".gitkeep"
        assert not gitkeep.exists(), (
            f"Placeholder file {gitkeep} should have been removed after copying real files into {directory}/."
        )
