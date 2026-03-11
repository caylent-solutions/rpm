"""Tests for clean core business logic."""

import pathlib
from unittest.mock import patch

import pytest

from rpm_cli.core.clean import (
    clean,
    remove_marketplace_dir,
    remove_packages_dir,
    remove_rpm_dir,
)


@pytest.mark.unit
class TestDirectoryRemoval:
    def test_removes_marketplace(self, tmp_path: pathlib.Path) -> None:
        mp = tmp_path / "mp"
        mp.mkdir()
        (mp / "file.txt").write_text("content")
        remove_marketplace_dir(mp)
        assert not mp.exists()

    def test_marketplace_missing_ok(self, tmp_path: pathlib.Path) -> None:
        remove_marketplace_dir(tmp_path / "nonexistent")

    def test_removes_packages(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / ".packages").mkdir()
        remove_packages_dir(tmp_path)
        assert not (tmp_path / ".packages").exists()

    def test_packages_missing_ok(self, tmp_path: pathlib.Path) -> None:
        remove_packages_dir(tmp_path)

    def test_removes_rpm(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / ".rpm").mkdir()
        remove_rpm_dir(tmp_path)
        assert not (tmp_path / ".rpm").exists()

    def test_rpm_missing_ok(self, tmp_path: pathlib.Path) -> None:
        remove_rpm_dir(tmp_path)


@pytest.mark.unit
class TestCleanLifecycle:
    def test_marketplace_false_skips_uninstall(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_MARKETPLACE_INSTALL=false\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        (tmp_path / ".packages").mkdir()
        (tmp_path / ".rpm").mkdir()
        with patch("rpm_cli.core.clean.uninstall_marketplace_plugins") as mock_uninstall:
            clean(rpmenv)
            mock_uninstall.assert_not_called()
        assert not (tmp_path / ".packages").exists()
        assert not (tmp_path / ".rpm").exists()

    def test_marketplace_true_missing_dir_exits(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_MARKETPLACE_INSTALL=true\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        with pytest.raises(SystemExit):
            clean(rpmenv)

    def test_order_of_operations(self, tmp_path: pathlib.Path) -> None:
        mp_dir = tmp_path / ".mp"
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            f"CLAUDE_MARKETPLACES_DIR={mp_dir}\n"
            "RPM_MARKETPLACE_INSTALL=true\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        mp_dir.mkdir()
        (tmp_path / ".packages").mkdir()
        (tmp_path / ".rpm").mkdir()

        ops: list[str] = []

        def track_uninstall(marketplace_dir):
            ops.append("uninstall")

        orig_rmtree = __import__("shutil").rmtree

        def track_rm(path, ignore_errors=False):
            p = str(path)
            if ".mp" in p:
                ops.append("rm_mp")
            elif ".packages" in p:
                ops.append("rm_packages")
            elif ".rpm" in p:
                ops.append("rm_rpm")
            orig_rmtree(path, ignore_errors=ignore_errors)

        with (
            patch("rpm_cli.core.clean.uninstall_marketplace_plugins", side_effect=track_uninstall),
            patch("rpm_cli.core.clean.shutil.rmtree", side_effect=track_rm),
        ):
            clean(rpmenv)

        assert ops == ["uninstall", "rm_mp", "rm_packages", "rm_rpm"]
