"""Shared fixtures for rpm-cli tests."""

import pathlib

import pytest


@pytest.fixture()
def sample_rpmenv(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a sample two-source .rpmenv file."""
    rpmenv = tmp_path / ".rpmenv"
    rpmenv.write_text(
        "REPO_URL=https://example.com/org/repo-tool.git\n"
        "REPO_REV=v2.0.0\n"
        "GITBASE=https://example.com/org/\n"
        "CLAUDE_MARKETPLACES_DIR=.claude-marketplaces\n"
        "RPM_MARKETPLACE_INSTALL=false\n"
        "RPM_SOURCE_build_URL=https://example.com/org/build-repo.git\n"
        "RPM_SOURCE_build_REVISION=main\n"
        "RPM_SOURCE_build_PATH=repo-specs/common/meta.xml\n"
        "RPM_SOURCE_marketplaces_URL=https://example.com/org/mp-repo.git\n"
        "RPM_SOURCE_marketplaces_REVISION=main\n"
        "RPM_SOURCE_marketplaces_PATH=repo-specs/common/marketplaces.xml\n"
    )
    return rpmenv


@pytest.fixture()
def mock_git_ls_remote_output() -> str:
    """Sample git ls-remote --tags output."""
    return (
        "abc123\trefs/tags/1.0.0\n"
        "def456\trefs/tags/1.0.1\n"
        "ghi789\trefs/tags/1.1.0\n"
        "jkl012\trefs/tags/2.0.0\n"
        "mno345\trefs/tags/2.0.0^{}\n"
    )
