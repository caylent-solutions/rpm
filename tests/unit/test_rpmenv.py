"""Tests for the rpmenv parser module."""

import os
import pathlib

import pytest

from rpm_cli.core.rpmenv import parse_rpmenv, validate_sources


@pytest.mark.unit
class TestValidParsing:
    """Verify valid .rpmenv parsing."""

    def test_parses_rpm_sources(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
            "RPM_SOURCE_marketplaces_URL=https://example.com\n"
            "RPM_SOURCE_marketplaces_REVISION=main\n"
            "RPM_SOURCE_marketplaces_PATH=mp.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["RPM_SOURCES"] == ["build", "marketplaces"]
        assert "build" in result["sources"]
        assert "marketplaces" in result["sources"]

    def test_parses_globals(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "REPO_URL=https://example.com\n"
            "REPO_REV=v2.0.0\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["globals"]["REPO_URL"] == "https://example.com"
        assert result["globals"]["REPO_REV"] == "v2.0.0"

    def test_parses_marketplace_bool(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_MARKETPLACE_INSTALL=true\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["RPM_MARKETPLACE_INSTALL"] is True


@pytest.mark.unit
class TestShellExpansion:
    """Verify ${VAR} expansion."""

    def test_expands_home(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "CLAUDE_DIR=${HOME}/.claude\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["globals"]["CLAUDE_DIR"] == f"{os.environ['HOME']}/.claude"

    def test_undefined_var_raises(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "BAD=${UNDEFINED_XYZ_12345}\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        with pytest.raises(ValueError, match="UNDEFINED_XYZ_12345"):
            parse_rpmenv(rpmenv)


@pytest.mark.unit
class TestEnvOverrides:
    """Verify environment variable overrides."""

    def test_env_overrides_file(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "REPO_REV=v1.0.0\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        monkeypatch.setenv("REPO_REV", "override")
        result = parse_rpmenv(rpmenv)
        assert result["globals"]["REPO_REV"] == "override"


@pytest.mark.unit
class TestValidation:
    """Verify validation errors."""

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_rpmenv(pathlib.Path("/nonexistent/.rpmenv"))

    def test_missing_sources_raises(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text("REPO_URL=https://example.com\n")
        with pytest.raises(ValueError, match="No sources found"):
            parse_rpmenv(rpmenv)

    def test_missing_source_var_raises(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text("RPM_SOURCE_build_URL=https://example.com\n")
        with pytest.raises(ValueError, match="RPM_SOURCE_build_REVISION"):
            parse_rpmenv(rpmenv)

    def test_validate_sources_direct(self) -> None:
        expanded = {
            "RPM_SOURCE_test_URL": "https://example.com",
            "RPM_SOURCE_test_REVISION": "main",
            "RPM_SOURCE_test_PATH": "meta.xml",
        }
        validate_sources(expanded, ["test"])

    def test_validate_sources_missing(self) -> None:
        expanded = {"RPM_SOURCE_test_URL": "https://example.com"}
        with pytest.raises(ValueError, match="RPM_SOURCE_test_REVISION"):
            validate_sources(expanded, ["test"])


@pytest.mark.unit
class TestEdgeCases:
    """Verify edge case handling."""

    def test_comments_ignored(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "# A comment\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        for key in result.get("globals", {}):
            assert not key.startswith("#")

    def test_value_with_equals(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_SOURCE_build_URL=https://example.com?a=1\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["sources"]["build"]["url"] == "https://example.com?a=1"

    def test_rpm_sources_present_raises_error(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_SOURCES=build\n"
            "RPM_SOURCE_build_URL=https://example.com\n"
            "RPM_SOURCE_build_REVISION=main\n"
            "RPM_SOURCE_build_PATH=meta.xml\n"
        )
        with pytest.raises(ValueError, match="no longer supported"):
            parse_rpmenv(rpmenv)

    def test_auto_discovery_alphabetical_order(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_SOURCE_beta_URL=https://example.com/beta.git\n"
            "RPM_SOURCE_beta_REVISION=main\n"
            "RPM_SOURCE_beta_PATH=meta.xml\n"
            "RPM_SOURCE_alpha_URL=https://example.com/alpha.git\n"
            "RPM_SOURCE_alpha_REVISION=main\n"
            "RPM_SOURCE_alpha_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["RPM_SOURCES"] == ["alpha", "beta"]

    def test_marketplace_defaults_false(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_SOURCE_build_URL=https://example.com\nRPM_SOURCE_build_REVISION=main\nRPM_SOURCE_build_PATH=meta.xml\n"
        )
        result = parse_rpmenv(rpmenv)
        assert result["RPM_MARKETPLACE_INSTALL"] is False
