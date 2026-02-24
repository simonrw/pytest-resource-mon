# pytest-resource-mon

A pytest plugin that snapshots system resources (CPU, memory, disk) for every test and ships the metrics to [Tinybird](https://www.tinybird.co/) or a local file.

## Quick Start

### Install

```bash
pip install pytest-resource-mon
```

### Write metrics to a local file

```bash
pytest --tinybird-file metrics.ndjson
```

### Send metrics to Tinybird

```bash
export TINYBIRD_WRITE_TOKEN=your-token
pytest
```

The plugin activates automatically when the token is set.

## Documentation

Full documentation is available at **https://simonrw.github.io/pytest-resource-mon/**.
