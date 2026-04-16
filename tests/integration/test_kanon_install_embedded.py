"""Integration tests for kanon install lifecycle using embedded Python API (8 tests).

Verifies that install uses the embedded Python API exclusively (no subprocess to
an external repo binary), works without pipx, works without repo on PATH, and
handles version constraints, deprecation warnings, subdirectory auto-discovery,
and KANON_MARKETPLACE_INSTALL=false correctly.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kanon_cli.commands.install import _run as install_run
from kanon_cli.core.install import install


def _write_kanonenv(directory: Path, content: str) -> Path:
    """Write a .kanon file in directory and return its path."""
    kanonenv = directory / ".kanon"
    kanonenv.write_text(content)
    return kanonenv


def _minimal_kanonenv_content(name: str = "primary") -> str:
    """Return a minimal .kanon content string for a single source."""
    return (
        f"KANON_SOURCE_{name}_URL=https://example.com/repo.git\n"
        f"KANON_SOURCE_{name}_REVISION=main\n"
        f"KANON_SOURCE_{name}_PATH=meta.xml\n"
    )


@pytest.mark.integration
class TestInstallUsesEmbeddedPythonAPI:
    """AC-FUNC-004: Install uses embedded Python API, not subprocess to repo binary."""

    def test_install_uses_embedded_python_api_not_subprocess(self, tmp_path: Path) -> None:
        """Verify install calls kanon_cli.repo.repo_init/envsubst/sync (Python API),
        not subprocess.run(['repo', ...]) or any shell-out to an external binary.
        The canonical signal is that subprocess.run is never called with 'repo'
        as the first argument element.
        """
        kanonenv = _write_kanonenv(tmp_path, _minimal_kanonenv_content())

        subprocess_calls: list[list[str]] = []

        original_subprocess_run = __import__("subprocess").run

        def capturing_run(cmd, *args, **kwargs):
            if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "repo":
                subprocess_calls.append(list(cmd))
            # Allow git ls-remote through (used by version resolution)
            return original_subprocess_run(cmd, *args, **kwargs)

        with (
            patch("kanon_cli.repo.repo_init") as mock_init,
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
            patch("subprocess.run", side_effect=capturing_run),
        ):
            install(kanonenv)

        assert len(subprocess_calls) == 0, (
            f"Expected zero subprocess calls to 'repo' binary, but found: {subprocess_calls}"
        )
        mock_init.assert_called_once()


@pytest.mark.integration
class TestInstallWithoutPipx:
    """AC-FUNC-005: Install succeeds without pipx installed."""

    def test_install_succeeds_without_pipx(self, tmp_path: Path) -> None:
        """Verify install completes successfully when pipx is not on PATH."""
        kanonenv = _write_kanonenv(tmp_path, _minimal_kanonenv_content())

        def fake_which(cmd: str):
            if cmd == "pipx":
                return None
            return f"/usr/bin/{cmd}"

        with (
            patch("shutil.which", side_effect=fake_which),
            patch("kanon_cli.repo.repo_init"),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
        ):
            install(kanonenv)

        assert (tmp_path / ".kanon-data" / "sources" / "primary").is_dir()


@pytest.mark.integration
class TestInstallWithoutRepoOnPath:
    """AC-FUNC-006: Install succeeds without repo binary on PATH."""

    def test_install_succeeds_without_repo_on_path(self, tmp_path: Path) -> None:
        """Verify install completes when 'repo' is not present on PATH."""
        kanonenv = _write_kanonenv(tmp_path, _minimal_kanonenv_content())

        original_which = __import__("shutil").which

        def fake_which(cmd: str):
            if cmd == "repo":
                return None
            return original_which(cmd)

        with (
            patch("shutil.which", side_effect=fake_which),
            patch("kanon_cli.repo.repo_init"),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
        ):
            install(kanonenv)

        assert (tmp_path / ".gitignore").is_file()
        gitignore_content = (tmp_path / ".gitignore").read_text()
        assert ".packages/" in gitignore_content
        assert ".kanon-data/" in gitignore_content


@pytest.mark.integration
class TestInstallVersionConstraintResolution:
    """AC-FUNC-011: Install with version constraint resolves to correct tag."""

    def test_install_version_constraint_resolves_to_correct_tag(self, tmp_path: Path) -> None:
        """Verify that a KANON_SOURCE_*_REVISION with a PEP 440 constraint
        resolves to the best matching tag via git ls-remote before repo_init is called.
        """
        kanonenv = _write_kanonenv(
            tmp_path,
            (
                "KANON_SOURCE_primary_URL=https://example.com/repo.git\n"
                "KANON_SOURCE_primary_REVISION=refs/tags/~=1.0.0\n"
                "KANON_SOURCE_primary_PATH=meta.xml\n"
            ),
        )

        captured_revision: list[str] = []

        def fake_repo_init(repo_dir: str, url: str, revision: str, manifest_path: str, repo_rev: str = "") -> None:
            captured_revision.append(revision)

        tags_output = "abc123\trefs/tags/1.0.0\ndef456\trefs/tags/1.0.3\nghi789\trefs/tags/2.0.0\n"
        mock_ls_remote = MagicMock(returncode=0, stdout=tags_output, stderr="")

        with (
            patch("kanon_cli.repo.repo_init", side_effect=fake_repo_init),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
            patch("kanon_cli.version.subprocess.run", return_value=mock_ls_remote),
        ):
            install(kanonenv)

        assert len(captured_revision) == 1, "repo_init should have been called once"
        assert captured_revision[0] == "refs/tags/1.0.3", (
            f"Expected constraint '~=1.0.0' to resolve to 'refs/tags/1.0.3', but got '{captured_revision[0]}'"
        )


@pytest.mark.integration
class TestInstallDeprecationWarnings:
    """AC-FUNC-012: Install with REPO_URL or REPO_REV emits deprecation warning to stderr."""

    def test_install_repo_url_emits_deprecation_warning(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Verify that REPO_URL in .kanon produces a deprecation warning on stderr."""
        kanonenv = _write_kanonenv(
            tmp_path,
            (
                "REPO_URL=https://example.com/old.git\n"
                "KANON_SOURCE_primary_URL=https://example.com/repo.git\n"
                "KANON_SOURCE_primary_REVISION=main\n"
                "KANON_SOURCE_primary_PATH=meta.xml\n"
            ),
        )

        args = MagicMock()
        args.kanonenv_path = kanonenv

        with (
            patch("kanon_cli.repo.repo_init"),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
        ):
            install_run(args)

        captured = capsys.readouterr()
        assert "REPO_URL" in captured.err, (
            f"Expected deprecation warning mentioning 'REPO_URL' in stderr, but got: {captured.err!r}"
        )
        assert "Deprecation" in captured.err or "deprecated" in captured.err.lower(), (
            f"Expected 'Deprecation' in stderr warning, got: {captured.err!r}"
        )

    def test_install_repo_rev_emits_deprecation_warning(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Verify that REPO_REV in .kanon produces a deprecation warning on stderr."""
        kanonenv = _write_kanonenv(
            tmp_path,
            (
                "REPO_REV=v2.0.0\n"
                "KANON_SOURCE_primary_URL=https://example.com/repo.git\n"
                "KANON_SOURCE_primary_REVISION=main\n"
                "KANON_SOURCE_primary_PATH=meta.xml\n"
            ),
        )

        args = MagicMock()
        args.kanonenv_path = kanonenv

        with (
            patch("kanon_cli.repo.repo_init"),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
        ):
            install_run(args)

        captured = capsys.readouterr()
        assert "REPO_REV" in captured.err, (
            f"Expected deprecation warning mentioning 'REPO_REV' in stderr, but got: {captured.err!r}"
        )


@pytest.mark.integration
class TestInstallSubdirectoryAutoDiscovery:
    """AC-FUNC-013: Install from subdirectory auto-discovers .kanon in parent and installs there."""

    def test_install_from_subdirectory_auto_discovers_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that running install from a subdirectory finds the .kanon in
        a parent directory and writes output files (e.g. .gitignore) relative to
        that parent directory -- not the subdirectory.
        """
        _write_kanonenv(tmp_path, _minimal_kanonenv_content())

        subdir = tmp_path / "subproject" / "nested"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        from kanon_cli.core.discover import find_kanonenv

        discovered = find_kanonenv(start_dir=subdir)
        assert discovered.parent == tmp_path.resolve(), (
            f"Auto-discovery should find .kanon in parent {tmp_path}, but found it in {discovered.parent}"
        )

        with (
            patch("kanon_cli.repo.repo_init"),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
        ):
            install(discovered)

        assert (tmp_path / ".gitignore").is_file(), (
            "install() should write .gitignore relative to the .kanon parent directory"
        )
        assert (tmp_path / ".kanon-data" / "sources" / "primary").is_dir(), (
            "install() should create .kanon-data/ relative to the .kanon parent directory"
        )


@pytest.mark.integration
class TestInstallMarketplaceDisabled:
    """AC-FUNC-014: Install with KANON_MARKETPLACE_INSTALL=false does not invoke claude commands."""

    def test_install_marketplace_false_no_claude_commands(self, tmp_path: Path) -> None:
        """Verify that when KANON_MARKETPLACE_INSTALL is false (the default),
        no claude CLI commands are invoked.
        """
        kanonenv = _write_kanonenv(
            tmp_path,
            (
                "KANON_MARKETPLACE_INSTALL=false\n"
                "KANON_SOURCE_primary_URL=https://example.com/repo.git\n"
                "KANON_SOURCE_primary_REVISION=main\n"
                "KANON_SOURCE_primary_PATH=meta.xml\n"
            ),
        )

        claude_calls: list[list[str]] = []

        original_subprocess_run = __import__("subprocess").run

        def capturing_run(cmd, *args, **kwargs):
            if isinstance(cmd, (list, tuple)) and cmd and "claude" in str(cmd[0]):
                claude_calls.append(list(cmd))
            return original_subprocess_run(cmd, *args, **kwargs)

        with (
            patch("kanon_cli.repo.repo_init"),
            patch("kanon_cli.repo.repo_envsubst"),
            patch("kanon_cli.repo.repo_sync"),
            patch("subprocess.run", side_effect=capturing_run),
        ):
            install(kanonenv)

        assert len(claude_calls) == 0, (
            f"Expected no claude CLI subprocess calls when KANON_MARKETPLACE_INSTALL=false, but got: {claude_calls}"
        )
