# Configuration

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--tinybird-batch-size` | `50` | Number of test records to buffer before sending a batch. |
| `--tinybird-disable` | `false` | Disable the plugin entirely. |
| `--tinybird-file` | _(none)_ | Write NDJSON metrics to a local file instead of sending over HTTP. |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TINYBIRD_WRITE_TOKEN` | No | _(none)_ | Tinybird auth token. When set, the plugin sends metrics over HTTP. |
| `TINYBIRD_API_URL` | No | `https://api.tinybird.co` | Tinybird API base URL. Only used when `TINYBIRD_WRITE_TOKEN` is set. |

## Activation Logic

```
if --tinybird-disable:
    plugin does not register

elif TINYBIRD_WRITE_TOKEN is set:
    use Tinybird HTTP writer

elif --tinybird-file is set:
    use local file writer

else:
    plugin does not register
```

`TINYBIRD_WRITE_TOKEN` takes priority over `--tinybird-file`. If both are set, the HTTP writer is used.
