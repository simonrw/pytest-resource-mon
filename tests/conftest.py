import json

import pytest

pytest_plugins = ["pytester"]


class FakeWriter:
    """Captures rows sent by the plugin for assertion."""

    def __init__(self, *, fail_count=0):
        self.rows = []
        self.call_count = 0
        self._fail_count = fail_count

    def send(self, rows):
        self.call_count += 1
        if self.call_count <= self._fail_count:
            raise ConnectionError("simulated failure")
        self.rows.extend(rows)


@pytest.fixture
def fake_writer():
    return FakeWriter()


@pytest.fixture
def clear_tinybird_env(monkeypatch):
    """Ensure no Tinybird env vars leak into tests."""
    monkeypatch.delenv("TINYBIRD_WRITE_TOKEN", raising=False)
    monkeypatch.delenv("TINYBIRD_API_URL", raising=False)
