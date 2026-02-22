# Metrics Schema

The `ci_test_metrics` datasource stores all events. The schema is sorted by `(timestamp, test_nodeid)`.

## Event Types

Every record has an `event_type` field. The plugin emits three types:

| Event Type | `test_nodeid` | When |
|-----------|---------------|------|
| `session_start` | `__session__` | Beginning of the pytest session |
| `test` | Full node ID (e.g. `tests/test_example.py::test_one`) | After each test's teardown |
| `session_end` | `__session__` | End of the pytest session |

## Full Schema

| Field | Type | Description | Events |
|-------|------|-------------|--------|
| `event_type` | String | `session_start`, `test`, or `session_end` | all |
| `test_nodeid` | String | Test node ID or `__session__` | all |
| `timestamp` | DateTime64(3) | UTC timestamp (ISO 8601) | all |
| `batch_num` | Int32 | Batch sequence number | `test` |
| `duration_s` | Float64 | Test wall-clock duration in seconds | `test` |
| `cpu_before` | Float64 | CPU usage % before test | `test` |
| `cpu_after` | Float64 | CPU usage % after test | `test` |
| `cpu_count` | Int32 | Logical CPU count | `session_start`, `session_end` |
| `mem_total_bytes` | Int64 | Total physical memory in bytes | `session_start`, `session_end` |
| `mem_available_before` | Int64 | Available memory before test (bytes) | `test` |
| `mem_available_after` | Int64 | Available memory after test (bytes) | `test` |
| `mem_percent_before` | Float64 | Memory usage % before test | `test` |
| `mem_percent_after` | Float64 | Memory usage % after test | `test` |
| `disk_total_bytes` | Int64 | Total disk space in bytes | `session_start`, `session_end` |
| `disk_free_before` | Int64 | Free disk space before test (bytes) | `test` |
| `disk_free_after` | Int64 | Free disk space after test (bytes) | `test` |
| `disk_percent_before` | Float64 | Disk usage % before test | `test` |
| `disk_percent_after` | Float64 | Disk usage % after test | `test` |
| `exit_status` | Int32 | Pytest exit code | `session_end` |
| `gh_run_id` | String | GitHub Actions run ID | all |
| `gh_sha` | String | Git commit SHA | all |
| `gh_ref_name` | String | Branch or tag name | all |
| `gh_workflow` | String | Workflow name | all |
| `gh_job` | String | Job ID | all |
| `gh_actor` | String | Actor who triggered the run | all |
| `gh_repository` | String | Repository (owner/repo) | all |
| `gh_run_attempt` | String | Run attempt number | all |
