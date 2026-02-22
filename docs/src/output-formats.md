# Output Formats

The plugin supports two output backends: Tinybird HTTP and local file.

## Tinybird HTTP

Activated when `TINYBIRD_WRITE_TOKEN` is set.

Sends NDJSON payloads to the Tinybird Events API:

```
POST {TINYBIRD_API_URL}/v0/events?name=ci_test_metrics
Authorization: Bearer {TINYBIRD_WRITE_TOKEN}
Content-Type: application/x-ndjson
```

### Batching

Test records are buffered and sent in batches controlled by `--tinybird-batch-size` (default: 50). Session start and session end events are sent immediately (not batched).

Each record in a batch is stamped with a `batch_num` field that increments per flush.

### Retries

If a request fails, the plugin retries **once**. If the retry also fails, the batch is dropped and a warning is logged. Failures never break the test run.

## Local File

Activated when `--tinybird-file` is provided (and `TINYBIRD_WRITE_TOKEN` is not set).

```bash
pytest --tinybird-file metrics.ndjson
```

Writes one JSON object per line (NDJSON format). The file is opened in **append mode**, so multiple runs accumulate in the same file.

### Example Output

```json
{"event_type": "session_start", "test_nodeid": "__session__", "timestamp": "2025-01-15T10:30:00+00:00", "cpu_count": 8, "mem_total_bytes": 17179869184, "disk_total_bytes": 499963174912, "gh_run_id": "", "gh_sha": "", ...}
{"event_type": "test", "test_nodeid": "tests/test_example.py::test_one", "timestamp": "2025-01-15T10:30:01+00:00", "duration_s": 0.1234, "cpu_before": 12.5, "cpu_after": 15.0, "mem_available_before": 8589934592, "mem_available_after": 8489934592, "batch_num": 1, ...}
{"event_type": "session_end", "test_nodeid": "__session__", "timestamp": "2025-01-15T10:30:05+00:00", "exit_status": 0, "cpu_count": 8, "mem_total_bytes": 17179869184, "disk_total_bytes": 499963174912, ...}
```
