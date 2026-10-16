"""Reuse the browser tool test isolation (fresh Runner singleton, offline connectivity check)."""
import pytest

from tests.browser_tool.conftest import offline_internet_check, reset_runner_singleton  # noqa: F401


@pytest.fixture(autouse=True)
def run_in_tmp_dir(tmp_path, monkeypatch):
    """These tests use relative result paths (test.json); keep them out of the repo."""
    monkeypatch.chdir(tmp_path)
