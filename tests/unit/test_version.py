"""Tests for fuzzy version resolution."""

from unittest.mock import MagicMock, patch

import pytest

from rpm_cli.version import _list_tags, _parse_tag_versions, resolve_version


@pytest.mark.unit
class TestResolveVersionPassthrough:
    """Verify plain branch/tag names pass through unchanged."""

    @pytest.mark.parametrize(
        "rev_spec",
        ["main", "caylent-2.0.0", "v1.0.0", "some-branch"],
        ids=["main", "caylent-tag", "v-prefixed", "branch"],
    )
    def test_passthrough(self, rev_spec: str) -> None:
        result = resolve_version("https://example.com/repo.git", rev_spec)
        assert result == rev_spec


@pytest.mark.unit
class TestResolveVersionPep440:
    """Verify PEP 440 specifier resolution."""

    def _mock_ls_remote(self, tags: list[str]):
        output = "\n".join(f"abc123\trefs/tags/{t}" for t in tags)
        mock = MagicMock(returncode=0, stdout=output, stderr="")
        return mock

    def test_compatible_release(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = self._mock_ls_remote(["1.0.0", "1.0.3", "1.1.0", "2.0.0"])
            result = resolve_version("https://example.com/repo.git", "~=1.0.0")
            assert result == "1.0.3"

    def test_range_specifier(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = self._mock_ls_remote(["1.0.0", "1.5.0", "2.0.0"])
            result = resolve_version("https://example.com/repo.git", ">=1.0.0,<2.0.0")
            assert result == "1.5.0"

    def test_exact_match(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = self._mock_ls_remote(["1.0.0", "1.2.3", "2.0.0"])
            result = resolve_version("https://example.com/repo.git", "==1.2.3")
            assert result == "1.2.3"

    def test_wildcard_returns_latest(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = self._mock_ls_remote(["1.0.0", "2.0.0", "3.0.0"])
            result = resolve_version("https://example.com/repo.git", "*")
            assert result == "3.0.0"

    def test_no_match_exits(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = self._mock_ls_remote(["1.0.0", "2.0.0"])
            with pytest.raises(SystemExit):
                resolve_version("https://example.com/repo.git", "==9.9.9")

    def test_no_tags_exits(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with pytest.raises(SystemExit):
                resolve_version("https://example.com/repo.git", "~=1.0.0")

    def test_git_failure_exits(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="fatal: not found")
            with pytest.raises(SystemExit):
                resolve_version("https://example.com/repo.git", "~=1.0.0")


@pytest.mark.unit
class TestListTags:
    """Verify git ls-remote tag parsing."""

    def test_parses_tags(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc\trefs/tags/1.0.0\ndef\trefs/tags/2.0.0\nghi\trefs/tags/2.0.0^{}\n",
                stderr="",
            )
            tags = _list_tags("https://example.com/repo.git")
            assert tags == ["1.0.0", "2.0.0"]

    def test_empty_output(self) -> None:
        with patch("rpm_cli.version.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            tags = _list_tags("https://example.com/repo.git")
            assert tags == []


@pytest.mark.unit
class TestParseTagVersions:
    """Verify tag version parsing."""

    def test_parses_simple_versions(self) -> None:
        result = _parse_tag_versions(["1.0.0", "2.0.0", "not-a-version"])
        assert len(result) == 2

    def test_parses_path_prefixed_versions(self) -> None:
        result = _parse_tag_versions(["prefix/1.0.0", "prefix/2.0.0"])
        assert len(result) == 2
