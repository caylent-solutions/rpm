"""Tests for the configure command handler."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestCheckPipx:
    def test_pipx_missing_exits(self) -> None:
        from rpm_cli.commands.configure import _check_pipx

        with patch("rpm_cli.commands.configure.shutil.which", return_value=None):
            with pytest.raises(SystemExit):
                _check_pipx()

    def test_pipx_present_ok(self) -> None:
        from rpm_cli.commands.configure import _check_pipx

        with patch("rpm_cli.commands.configure.shutil.which", return_value="/usr/bin/pipx"):
            _check_pipx()


@pytest.mark.unit
class TestInstallRepoTool:
    def test_success(self) -> None:
        from rpm_cli.commands.configure import _install_repo_tool

        with patch("rpm_cli.commands.configure.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            _install_repo_tool("https://example.com/repo.git", "v2.0.0")
            cmd = mock_run.call_args[0][0]
            assert "pipx" in cmd
            assert "--force" in cmd

    def test_failure_exits(self) -> None:
        from rpm_cli.commands.configure import _install_repo_tool

        with patch("rpm_cli.commands.configure.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="error")
            with pytest.raises(SystemExit):
                _install_repo_tool("https://example.com/repo.git", "v2.0.0")
