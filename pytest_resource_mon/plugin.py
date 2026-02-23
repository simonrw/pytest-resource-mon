import json
import logging
import os
import time
import urllib.request
from datetime import datetime, timezone

import psutil
import pytest

logger = logging.getLogger(__name__)

_stash_key = pytest.StashKey[dict]()

_GH_ENV_VARS = {
    "GITHUB_RUN_ID": "gh_run_id",
    "GITHUB_SHA": "gh_sha",
    "GITHUB_REF_NAME": "gh_ref_name",
    "GITHUB_WORKFLOW": "gh_workflow",
    "GITHUB_JOB": "gh_job",
    "GITHUB_ACTOR": "gh_actor",
    "GITHUB_REPOSITORY": "gh_repository",
    "GITHUB_RUN_ATTEMPT": "gh_run_attempt",
}


def _take_snapshot():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_available_bytes": mem.available,
        "mem_percent": mem.percent,
        "disk_free_bytes": disk.free,
        "disk_percent": disk.percent,
    }


def _gh_context():
    return {v: os.environ.get(k, "") for k, v in _GH_ENV_VARS.items()}


class _TinybirdWriter:
    def __init__(self, token, api_url, datasource):
        self._url = f"{api_url}/v0/events?name={datasource}"
        self._token = token

    def send(self, rows):
        body = "\n".join(json.dumps(r) for r in rows).encode()
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/x-ndjson",
            },
        )
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp.read()
                return
            except Exception:
                if attempt == 0:
                    logger.warning("Tinybird send failed, retrying once")
                else:
                    logger.warning("Tinybird send failed after retry, dropping %d rows", len(rows))


class _FileWriter:
    def __init__(self, path):
        self._path = path

    def send(self, rows):
        with open(self._path, "a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")


class TinybirdMetricsPlugin:
    def __init__(self, writer, batch_size):
        self._writer = writer
        self._batch_size = batch_size
        self._buffer = []
        self._batch_num = 0
        self._gh = _gh_context()

    def pytest_sessionstart(self, session):
        # prime cpu_percent so the next call returns a meaningful value
        psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        record = {
            "event_type": "session_start",
            "test_nodeid": "__session__",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_count": psutil.cpu_count(),
            "mem_total_bytes": mem.total,
            "disk_total_bytes": disk.total,
            **self._gh,
        }
        self._send_rows([record])

    def pytest_runtest_setup(self, item):
        item.stash[_stash_key] = {
            "snapshot_before": _take_snapshot(),
            "t_start": time.monotonic(),
        }

    def pytest_runtest_teardown(self, item):
        stashed = item.stash.get(_stash_key, None)
        if stashed is None:
            return
        after = _take_snapshot()
        before = stashed["snapshot_before"]
        duration = time.monotonic() - stashed["t_start"]
        record = {
            "event_type": "test",
            "test_nodeid": item.nodeid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_s": round(duration, 4),
            "cpu_before": before["cpu_percent"],
            "cpu_after": after["cpu_percent"],
            "mem_available_before": before["mem_available_bytes"],
            "mem_available_after": after["mem_available_bytes"],
            "mem_percent_before": before["mem_percent"],
            "mem_percent_after": after["mem_percent"],
            "disk_free_before": before["disk_free_bytes"],
            "disk_free_after": after["disk_free_bytes"],
            "disk_percent_before": before["disk_percent"],
            "disk_percent_after": after["disk_percent"],
            **self._gh,
        }
        self._buffer.append(record)
        if len(self._buffer) >= self._batch_size:
            self._flush()

    def pytest_sessionfinish(self, session, exitstatus):
        if self._buffer:
            self._flush()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        record = {
            "event_type": "session_end",
            "test_nodeid": "__session__",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exit_status": exitstatus,
            "cpu_count": psutil.cpu_count(),
            "mem_total_bytes": mem.total,
            "disk_total_bytes": disk.total,
            **self._gh,
        }
        self._send_rows([record])

    def _flush(self):
        self._batch_num += 1
        for record in self._buffer:
            record["batch_num"] = self._batch_num
        self._send_rows(list(self._buffer))
        self._buffer.clear()

    def _send_rows(self, rows):
        try:
            self._writer.send(rows)
        except Exception as e:
            logger.warning("Failed to send %d rows", len(rows), exc_info=True)


def pytest_addoption(parser):
    group = parser.getgroup("tinybird-metrics", "Tinybird resource metrics")
    group.addoption(
        "--tinybird-batch-size",
        type=int,
        default=50,
        help="Number of test records to batch before sending (default: 50)",
    )
    group.addoption(
        "--tinybird-disable",
        action="store_true",
        default=False,
        help="Disable the Tinybird metrics plugin",
    )
    group.addoption(
        "--tinybird-file",
        default=None,
        help="Write NDJSON metrics to a local file instead of HTTP",
    )


def pytest_configure(config):
    if config.getoption("--tinybird-disable", default=False):
        return

    token = os.environ.get("TINYBIRD_WRITE_TOKEN")
    file_path = config.getoption("--tinybird-file", default=None)
    batch_size = config.getoption("--tinybird-batch-size", default=50)

    if token:
        api_url = os.environ.get("TINYBIRD_API_URL", "https://api.tinybird.co")
        writer = _TinybirdWriter(token, api_url, "ci_test_metrics")
    elif file_path:
        writer = _FileWriter(file_path)
    else:
        return

    plugin = TinybirdMetricsPlugin(writer, batch_size)
    config.pluginmanager.register(plugin, "tinybird-metrics")
