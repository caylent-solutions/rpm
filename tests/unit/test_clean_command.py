"""Tests for the clean command handler."""

import pathlib
import types
from unittest.mock import patch

import pytest

from rpm_cli.commands.clean import _run


@pytest.mark.unit
class TestCleanCommand:
    def test_delegates_to_core(self, tmp_path: pathlib.Path) -> None:
        rpmenv = tmp_path / ".rpmenv"
        rpmenv.write_text(
            "RPM_SOURCE_build_URL=https://example.com\nRPM_SOURCE_build_REVISION=main\nRPM_SOURCE_build_PATH=meta.xml\n"
        )
        args = types.SimpleNamespace(rpmenv_path=rpmenv)
        with patch("rpm_cli.commands.clean.clean") as mock_clean:
            _run(args)
            mock_clean.assert_called_once_with(rpmenv)
