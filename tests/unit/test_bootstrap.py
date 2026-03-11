"""Tests for the bootstrap module."""

import pathlib

import pytest

from rpm_cli.core.bootstrap import (
    _generate_rpmenv_template,
    bootstrap_runner,
    list_runners,
)
from rpm_cli.core.catalog import _get_bundled_catalog_dir


@pytest.mark.unit
class TestListRunners:
    """Verify list_runners returns available catalog entries."""

    def test_returns_make_and_gradle(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        runners = list_runners(catalog_dir)
        assert "make" in runners
        assert "gradle" in runners

    def test_returns_sorted_list(self) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        runners = list_runners(catalog_dir)
        assert runners == sorted(runners)


@pytest.mark.unit
class TestBootstrapMake:
    """Verify make runner bootstrapping."""

    def test_creates_makefile_and_rpmenv(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_runner("make", output, catalog_dir)
        assert (output / "Makefile").is_file()
        assert (output / ".rpmenv").is_file()

    def test_makefile_matches_catalog(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_runner("make", output, catalog_dir)
        expected = (catalog_dir / "make" / "Makefile").read_text()
        actual = (output / "Makefile").read_text()
        assert actual == expected


@pytest.mark.unit
class TestBootstrapGradle:
    """Verify gradle runner bootstrapping."""

    def test_creates_all_files(self, tmp_path: pathlib.Path) -> None:
        output = tmp_path / "project"
        catalog_dir = _get_bundled_catalog_dir()
        bootstrap_runner("gradle", output, catalog_dir)
        assert (output / "build.gradle").is_file()
        assert (output / "rpm-bootstrap.gradle").is_file()
        assert (output / ".rpmenv").is_file()


@pytest.mark.unit
class TestBootstrapConflicts:
    """Verify fail-fast on existing files."""

    def test_refuses_overwrite_existing_files(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "Makefile").write_text("existing")
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_runner("make", tmp_path, catalog_dir)

    def test_refuses_overwrite_existing_rpmenv(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / ".rpmenv").write_text("existing")
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_runner("make", tmp_path, catalog_dir)


@pytest.mark.unit
class TestBootstrapUnknownRunner:
    """Verify fail-fast on unknown runner."""

    def test_unknown_runner_fails(self, tmp_path: pathlib.Path) -> None:
        catalog_dir = _get_bundled_catalog_dir()
        with pytest.raises(SystemExit):
            bootstrap_runner("nonexistent", tmp_path, catalog_dir)


@pytest.mark.unit
class TestGeneratedRpmenv:
    """Verify generated .rpmenv template content."""

    def test_contains_placeholders(self) -> None:
        content = _generate_rpmenv_template()
        assert "<RPM_CLI_URL>" in content
        assert "<RPM_CLI_REV>" in content
        assert "<REPO_URL>" in content
        assert "<REPO_REV>" in content
        assert "<GITBASE>" in content
        assert "<SOURCE_URL>" in content
        assert "<SOURCE_REVISION>" in content
        assert "<SOURCE_MANIFEST_PATH>" in content

    def test_omits_rpm_sources(self) -> None:
        content = _generate_rpmenv_template()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not stripped.startswith("RPM_SOURCES=")

    def test_has_active_build_source(self) -> None:
        content = _generate_rpmenv_template()
        assert "RPM_SOURCE_build_URL=" in content

    def test_has_commented_marketplaces_source(self) -> None:
        content = _generate_rpmenv_template()
        assert "# RPM_SOURCE_marketplaces_URL=" in content

    def test_has_commented_tools_source(self) -> None:
        content = _generate_rpmenv_template()
        assert "# RPM_SOURCE_tools_URL=" in content

    def test_marketplace_install_defaults_false(self) -> None:
        content = _generate_rpmenv_template()
        assert "RPM_MARKETPLACE_INSTALL=false" in content
