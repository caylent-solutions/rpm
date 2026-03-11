"""Tests for marketplace XML validation."""

import textwrap
from pathlib import Path

import pytest

from rpm_cli.core.marketplace_validator import (
    _is_valid_revision,
    validate_include_chain,
    validate_linkfile_dest,
    validate_name_uniqueness,
    validate_tag_format,
)


def _write_xml(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + content)
    return path


@pytest.mark.unit
class TestLinkfileDest:
    def test_valid_dest(self, tmp_path: Path) -> None:
        xml = _write_xml(
            tmp_path / "m.xml",
            textwrap.dedent("""\
                <manifest>
                  <project name="proj" path=".packages/proj" remote="r" revision="main">
                    <linkfile src="s" dest="${CLAUDE_MARKETPLACES_DIR}/proj" />
                  </project>
                </manifest>
            """),
        )
        assert validate_linkfile_dest(xml) == []

    def test_invalid_dest(self, tmp_path: Path) -> None:
        xml = _write_xml(
            tmp_path / "m.xml",
            textwrap.dedent("""\
                <manifest>
                  <project name="proj" path=".packages/proj" remote="r" revision="main">
                    <linkfile src="s" dest="/bad/path" />
                  </project>
                </manifest>
            """),
        )
        errors = validate_linkfile_dest(xml)
        assert len(errors) == 1
        assert "proj" in errors[0]


@pytest.mark.unit
class TestIncludeChain:
    def test_valid_chain(self, tmp_path: Path) -> None:
        _write_xml(tmp_path / "root.xml", '<manifest><remote name="r" fetch="u" /></manifest>')
        _write_xml(tmp_path / "leaf.xml", '<manifest><include name="root.xml" /></manifest>')
        errors = validate_include_chain(tmp_path / "leaf.xml", tmp_path)
        assert errors == []

    def test_broken_reference(self, tmp_path: Path) -> None:
        _write_xml(tmp_path / "leaf.xml", '<manifest><include name="missing.xml" /></manifest>')
        errors = validate_include_chain(tmp_path / "leaf.xml", tmp_path)
        assert len(errors) > 0
        assert any("missing.xml" in e for e in errors)


@pytest.mark.unit
class TestNameUniqueness:
    def test_unique_passes(self, tmp_path: Path) -> None:
        f1 = _write_xml(
            tmp_path / "a" / "m.xml",
            '<manifest><project name="a" path=".packages/a" remote="r" revision="main" /></manifest>',
        )
        f2 = _write_xml(
            tmp_path / "b" / "m.xml",
            '<manifest><project name="b" path=".packages/b" remote="r" revision="main" /></manifest>',
        )
        assert validate_name_uniqueness([f1, f2]) == []

    def test_duplicate_detected(self, tmp_path: Path) -> None:
        f1 = _write_xml(
            tmp_path / "a" / "m.xml",
            '<manifest><project name="dup" path=".packages/dup" remote="r" revision="main" /></manifest>',
        )
        f2 = _write_xml(
            tmp_path / "b" / "m.xml",
            '<manifest><project name="dup" path=".packages/dup" remote="r" revision="main" /></manifest>',
        )
        errors = validate_name_uniqueness([f1, f2])
        assert len(errors) > 0


@pytest.mark.unit
class TestTagFormat:
    @pytest.mark.parametrize(
        "revision",
        ["refs/tags/example/proj/1.0.0", "~=1.2.0", "*", "main", ">=1.0.0", ">=1.0.0,<2.0.0"],
    )
    def test_valid_revisions(self, revision: str) -> None:
        assert _is_valid_revision(revision)

    @pytest.mark.parametrize(
        "revision",
        ["refs/tags/no-semver", "random-string", "refs/heads/main"],
    )
    def test_invalid_revisions(self, revision: str) -> None:
        assert not _is_valid_revision(revision)

    def test_validate_tag_format_valid(self, tmp_path: Path) -> None:
        f1 = _write_xml(
            tmp_path / "m.xml",
            '<manifest><project name="p" path=".packages/p" remote="r" revision="refs/tags/ex/1.0.0" /></manifest>',
        )
        assert validate_tag_format([f1]) == []

    def test_validate_tag_format_invalid(self, tmp_path: Path) -> None:
        f1 = _write_xml(
            tmp_path / "m.xml",
            '<manifest><project name="p" path=".packages/p" remote="r" revision="invalid" /></manifest>',
        )
        errors = validate_tag_format([f1])
        assert len(errors) > 0
