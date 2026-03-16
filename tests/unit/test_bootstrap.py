"""Tests for the bootstrap module."""

import pathlib

import pytest

from rpm_cli.core.bootstrap import (
    _print_next_steps,
    bootstrap_package,
    list_packages,
)
from rpm_cli.core.catalog import _get_bundled_catalog_dir


@pytest.mark.unit
class TestListPackages:
    """Verify list_packages returns available catalog entries."""

    def test_returns_make_gradle_and_rpm(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        packages = list_packages(catalog_dir)
        assert "make" in packages
        assert "gradle" in packages
        assert "rpm" in packages

    def test_returns_sorted_list(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        packages = list_packages(catalog_dir)
        assert packages == sorted(packages)

    def test_alphabetical_order_is_gradle_make_rpm(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        packages = list_packages(catalog_dir)
        assert packages == ["gradle", "make", "rpm"]


@pytest.mark.unit
class TestBootstrapMake:
    """Verify make catalog entry package bootstrapping."""

    def test_creates_makefile_and_rpmenv(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("make", output, catalog_dir)
        assert (output / "Makefile").is_file()
        assert (output / ".rpmenv").is_file()
        assert (output / "rpm-readme.md").is_file()

    def test_readme_mentions_make(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("make", output, catalog_dir)
        content = (output / "rpm-readme.md").read_text()
        assert "make rpmConfigure" in content
        assert "Prerequisites" in content

    def test_makefile_matches_catalog(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("make", output, catalog_dir)
        expected = (catalog_dir / "make" / "Makefile").read_text()
        actual = (output / "Makefile").read_text()
        assert actual == expected

    def test_rpmenv_matches_catalog(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("make", output, catalog_dir)
        expected = (catalog_dir / "make" / ".rpmenv").read_text()
        actual = (output / ".rpmenv").read_text()
        assert actual == expected


@pytest.mark.unit
class TestBootstrapGradle:
    """Verify gradle catalog entry package bootstrapping."""

    def test_creates_all_files(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("gradle", output, catalog_dir)
        assert (output / "build.gradle").is_file()
        assert (output / "rpm-bootstrap.gradle").is_file()
        assert (output / ".rpmenv").is_file()
        assert (output / "rpm-readme.md").is_file()

    def test_readme_mentions_gradle(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("gradle", output, catalog_dir)
        content = (output / "rpm-readme.md").read_text()
        assert "./gradlew rpmConfigure" in content
        assert "gradle wrapper" in content
        assert "Java 17+" in content

    def test_rpmenv_matches_catalog(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("gradle", output, catalog_dir)
        expected = (catalog_dir / "gradle" / ".rpmenv").read_text()
        actual = (output / ".rpmenv").read_text()
        assert actual == expected


@pytest.mark.unit
class TestBootstrapRpm:
    """Verify rpm catalog entry package produces .rpmenv and rpm-readme.md."""

    def test_creates_rpmenv_and_readme(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("rpm", output, catalog_dir)
        assert (output / ".rpmenv").is_file()
        assert (output / "rpm-readme.md").is_file()
        created_files = sorted(f.name for f in output.iterdir())
        assert created_files == [".rpmenv", "rpm-readme.md"]

    def test_rpmenv_matches_catalog(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("rpm", output, catalog_dir)
        expected = (catalog_dir / "rpm" / ".rpmenv").read_text()
        actual = (output / ".rpmenv").read_text()
        assert actual == expected

    def test_does_not_copy_gitkeep(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("rpm", output, catalog_dir)
        assert not (output / ".gitkeep").exists()

    def test_readme_mentions_standalone(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_package("rpm", output, catalog_dir)
        content = (output / "rpm-readme.md").read_text()
        assert "rpm configure .rpmenv" in content


@pytest.mark.unit
class TestBootstrapConflicts:
    """Verify fail-fast on existing files."""

    def test_refuses_overwrite_existing_files(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "Makefile").write_text("existing")
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_package("make", tmp_path, catalog_dir)

    def test_refuses_overwrite_existing_rpmenv(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / ".rpmenv").write_text("existing")
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_package("make", tmp_path, catalog_dir)

    def test_rpm_package_refuses_overwrite_existing_rpmenv(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / ".rpmenv").write_text("existing")
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_package("rpm", tmp_path, catalog_dir)


@pytest.mark.unit
class TestBootstrapUnknownPackage:
    """Verify fail-fast on unknown package."""

    def test_unknown_package_fails(self, tmp_path: pathlib.Path) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_package("nonexistent", tmp_path, catalog_dir)


@pytest.mark.unit
class TestCatalogRpmenvFiles:
    """Verify each catalog entry includes a pre-configured .rpmenv."""

    def test_make_rpmenv_has_no_placeholders(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        content = (catalog_dir / "make" / ".rpmenv").read_text()
        assert "<RPM_CLI_URL>" not in content
        assert "<GITBASE>" not in content
        assert "<SOURCE_URL>" not in content
        assert "REPO_URL=" in content
        assert "RPM_SOURCE_packages_URL=" in content

    def test_gradle_rpmenv_has_no_placeholders(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        content = (catalog_dir / "gradle" / ".rpmenv").read_text()
        assert "<RPM_CLI_URL>" not in content
        assert "<GITBASE>" not in content
        assert "<SOURCE_URL>" not in content
        assert "REPO_URL=" in content
        assert "RPM_SOURCE_packages_URL=" in content

    def test_rpm_rpmenv_has_no_placeholders(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        content = (catalog_dir / "rpm" / ".rpmenv").read_text()
        assert "<RPM_CLI_URL>" not in content
        assert "<GITBASE>" not in content
        assert "<SOURCE_URL>" not in content
        assert "REPO_URL=" in content
        assert "RPM_SOURCE_packages_URL=" in content


@pytest.mark.unit
class TestPrintNextSteps:
    """Verify post-bootstrap instructions vary by package."""

    def test_make_package_shows_make_command(self, tmp_path: pathlib.Path, capsys) -> None:
        _print_next_steps("make", tmp_path, ["Makefile", ".rpmenv"])
        output = capsys.readouterr().out
        assert "make rpmConfigure" in output
        assert "Commit .rpmenv and the catalog entry files" in output

    def test_gradle_package_shows_gradlew_command(self, tmp_path: pathlib.Path, capsys) -> None:
        _print_next_steps("gradle", tmp_path, ["build.gradle", ".rpmenv"])
        output = capsys.readouterr().out
        assert "./gradlew rpmConfigure" in output
        assert "Commit .rpmenv and the catalog entry files" in output

    def test_rpm_package_shows_rpm_command(self, tmp_path: pathlib.Path, capsys) -> None:
        _print_next_steps("rpm", tmp_path, [".rpmenv"])
        output = capsys.readouterr().out
        assert "rpm configure .rpmenv" in output
        assert "Commit .rpmenv to your repository" in output

    def test_rpm_package_does_not_mention_catalog_entry_files(self, tmp_path: pathlib.Path, capsys) -> None:
        _print_next_steps("rpm", tmp_path, [".rpmenv"])
        output = capsys.readouterr().out
        assert "catalog entry files" not in output
