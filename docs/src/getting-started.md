# Getting Started

## Installation

```bash
pip install pytest-resource-mon
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add pytest-resource-mon
```

The plugin requires Python 3.9+ and depends on `pytest>=7.0` and `psutil>=5.9`.

## Quick Start

### Write metrics to a local file

```bash
pytest --tinybird-file metrics.ndjson
```

This writes one NDJSON line per event to `metrics.ndjson`.

### Send metrics to Tinybird

```bash
export TINYBIRD_WRITE_TOKEN=your-token
pytest
```

The plugin activates automatically when `TINYBIRD_WRITE_TOKEN` is set.

### Disable the plugin

```bash
pytest --tinybird-disable
```

This flag prevents the plugin from registering, even if a token or file path is configured.

## Activation Rules

The plugin activates when **either** of these conditions is true:

1. The `TINYBIRD_WRITE_TOKEN` environment variable is set (Tinybird HTTP mode).
2. The `--tinybird-file` flag is provided (local file mode).

If `TINYBIRD_WRITE_TOKEN` is set, it takes priority over `--tinybird-file`. If neither is configured, the plugin does nothing.

Passing `--tinybird-disable` always prevents activation regardless of other settings.
