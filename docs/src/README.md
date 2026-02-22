# pytest-resource-mon

A pytest plugin that snapshots system resources (CPU, memory, disk) for every test and ships the metrics to [Tinybird](https://www.tinybird.co/) or a local file.

## Key Features

- **Per-test resource snapshots** — captures CPU, memory, and disk usage before and after each test.
- **Batched delivery** — groups test records into configurable batches to reduce network overhead.
- **CI context** — automatically captures GitHub Actions environment variables so metrics can be correlated with runs, commits, and workflows.
- **Flexible output** — send metrics to Tinybird over HTTP or write NDJSON to a local file.

## How It Works

The plugin emits three event types:

1. **`session_start`** — records total CPU count, memory, and disk at the beginning of the test session.
2. **`test`** — records before/after snapshots of CPU %, available memory, and free disk for each test, plus duration.
3. **`session_end`** — records final resource state and the pytest exit status.

## Next Steps

See [Getting Started](getting-started.md) to install and run the plugin.
