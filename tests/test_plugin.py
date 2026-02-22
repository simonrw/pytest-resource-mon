import json
import urllib.error

import pytest

from pytest_tinybird_metrics.plugin import (
    TinybirdMetricsPlugin,
    _FileWriter,
    _TinybirdWriter,
    _gh_context,
    _take_snapshot,
)

from .conftest import FakeWriter


# --- Unit tests ---


class TestTakeSnapshot:
    def test_returns_expected_keys(self):
        snap = _take_snapshot()
        expected = {"cpu_percent", "mem_available_bytes", "mem_percent", "disk_free_bytes", "disk_percent"}
        assert snap.keys() == expected

    def test_values_are_numeric(self):
        snap = _take_snapshot()
        for v in snap.values():
            assert isinstance(v, (int, float))


class TestGhContext:
    def test_maps_env_vars(self, monkeypatch):
        monkeypatch.setenv("GITHUB_RUN_ID", "12345")
        monkeypatch.setenv("GITHUB_SHA", "abc123")
        monkeypatch.setenv("GITHUB_REPOSITORY", "org/repo")
        ctx = _gh_context()
        assert ctx["gh_run_id"] == "12345"
        assert ctx["gh_sha"] == "abc123"
        assert ctx["gh_repository"] == "org/repo"

    def test_missing_vars_are_empty_string(self, monkeypatch):
        for var in ["GITHUB_RUN_ID", "GITHUB_SHA", "GITHUB_REF_NAME",
                     "GITHUB_WORKFLOW", "GITHUB_JOB", "GITHUB_ACTOR",
                     "GITHUB_REPOSITORY", "GITHUB_RUN_ATTEMPT"]:
            monkeypatch.delenv(var, raising=False)
        ctx = _gh_context()
        assert all(v == "" for v in ctx.values())


class TestBatchFlushing:
    def test_flush_at_threshold(self, fake_writer):
        plugin = TinybirdMetricsPlugin(fake_writer, batch_size=2)
        plugin._buffer = [{"a": 1}, {"b": 2}]
        plugin._flush()
        assert len(fake_writer.rows) == 2
        assert plugin._batch_num == 1
        assert plugin._buffer == []

    def test_batch_num_increments(self, fake_writer):
        plugin = TinybirdMetricsPlugin(fake_writer, batch_size=2)
        plugin._buffer = [{"a": 1}]
        plugin._flush()
        plugin._buffer = [{"b": 2}]
        plugin._flush()
        assert plugin._batch_num == 2

    def test_flush_stamps_batch_num(self, fake_writer):
        plugin = TinybirdMetricsPlugin(fake_writer, batch_size=2)
        plugin._buffer = [{"a": 1}, {"b": 2}]
        plugin._flush()
        assert all(r["batch_num"] == 1 for r in fake_writer.rows)

    def test_send_failure_does_not_raise(self):
        writer = FakeWriter(fail_count=999)
        plugin = TinybirdMetricsPlugin(writer, batch_size=2)
        plugin._buffer = [{"a": 1}]
        # should not raise
        plugin._flush()


class TestTinybirdWriter:
    def test_retries_once_on_failure(self, monkeypatch):
        calls = []

        def mock_urlopen(req, timeout=None):
            calls.append(req)
            raise urllib.error.URLError("fail")

        monkeypatch.setattr("pytest_tinybird_metrics.plugin.urllib.request.urlopen", mock_urlopen)
        writer = _TinybirdWriter("tok", "https://api.tinybird.co", "ds")
        writer.send([{"x": 1}])
        assert len(calls) == 2  # initial + 1 retry

    def test_sends_ndjson(self, monkeypatch):
        captured = {}

        class FakeResponse:
            def read(self):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        def mock_urlopen(req, timeout=None):
            captured["body"] = req.data
            captured["headers"] = dict(req.headers)
            return FakeResponse()

        monkeypatch.setattr("pytest_tinybird_metrics.plugin.urllib.request.urlopen", mock_urlopen)
        writer = _TinybirdWriter("tok123", "https://api.tinybird.co", "ci_test_metrics")
        writer.send([{"a": 1}, {"b": 2}])
        lines = captured["body"].decode().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"a": 1}
        assert captured["headers"]["Content-type"] == "application/x-ndjson"


class TestFileWriter:
    def test_writes_ndjson(self, tmp_path):
        path = tmp_path / "metrics.ndjson"
        writer = _FileWriter(str(path))
        writer.send([{"a": 1}, {"b": 2}])
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"a": 1}

    def test_appends_on_multiple_calls(self, tmp_path):
        path = tmp_path / "metrics.ndjson"
        writer = _FileWriter(str(path))
        writer.send([{"a": 1}])
        writer.send([{"b": 2}])
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2


# --- Integration tests (pytester) ---


class TestPluginIntegration:
    SIMPLE_TEST = "def test_one(): pass\ndef test_two(): pass\n"

    def test_disabled_without_token(self, pytester, clear_tinybird_env):
        pytester.makepyfile(self.SIMPLE_TEST)
        result = pytester.runpytest()
        result.assert_outcomes(passed=2)

    def test_disabled_with_flag(self, pytester, monkeypatch):
        monkeypatch.setenv("TINYBIRD_WRITE_TOKEN", "fake-token")
        pytester.makepyfile(self.SIMPLE_TEST)
        result = pytester.runpytest("--tinybird-disable")
        result.assert_outcomes(passed=2)

    def test_file_writer_lifecycle(self, pytester, clear_tinybird_env, tmp_path):
        outfile = tmp_path / "out.ndjson"
        pytester.makepyfile(self.SIMPLE_TEST)
        result = pytester.runpytest("--tinybird-file", str(outfile))
        result.assert_outcomes(passed=2)

        lines = outfile.read_text().strip().split("\n")
        records = [json.loads(line) for line in lines]

        event_types = [r["event_type"] for r in records]
        assert event_types[0] == "session_start"
        assert event_types[-1] == "session_end"
        test_records = [r for r in records if r["event_type"] == "test"]
        assert len(test_records) == 2
        nodeids = {r["test_nodeid"] for r in test_records}
        assert "test_file_writer_lifecycle.py::test_one" in nodeids
        assert "test_file_writer_lifecycle.py::test_two" in nodeids

    def test_http_failure_does_not_break_tests(self, pytester, monkeypatch):
        # Point at a port that will refuse connections
        monkeypatch.setenv("TINYBIRD_WRITE_TOKEN", "fake-token")
        monkeypatch.setenv("TINYBIRD_API_URL", "http://127.0.0.1:1")
        pytester.makepyfile(self.SIMPLE_TEST)
        result = pytester.runpytest()
        result.assert_outcomes(passed=2)

    def test_batch_flushing_with_file(self, pytester, clear_tinybird_env, tmp_path):
        outfile = tmp_path / "out.ndjson"
        pytester.makepyfile(
            "def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n"
        )
        result = pytester.runpytest("--tinybird-file", str(outfile), "--tinybird-batch-size", "2")
        result.assert_outcomes(passed=3)

        records = [json.loads(line) for line in outfile.read_text().strip().split("\n")]
        test_records = [r for r in records if r["event_type"] == "test"]
        assert len(test_records) == 3
        # first 2 should have batch_num=1, last should have batch_num=2
        assert test_records[0]["batch_num"] == 1
        assert test_records[1]["batch_num"] == 1
        assert test_records[2]["batch_num"] == 2

    def test_session_end_has_exit_status(self, pytester, clear_tinybird_env, tmp_path):
        outfile = tmp_path / "out.ndjson"
        pytester.makepyfile("def test_pass(): pass\n")
        result = pytester.runpytest("--tinybird-file", str(outfile))
        result.assert_outcomes(passed=1)

        records = [json.loads(line) for line in outfile.read_text().strip().split("\n")]
        session_end = [r for r in records if r["event_type"] == "session_end"][0]
        assert session_end["exit_status"] == 0
