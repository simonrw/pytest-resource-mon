# GitHub Actions Integration

When running in GitHub Actions, the plugin automatically captures environment variables and includes them in every event record.

## Captured Variables

| GitHub Env Var | Metric Field | Description |
|---------------|--------------|-------------|
| `GITHUB_RUN_ID` | `gh_run_id` | Unique ID for the workflow run |
| `GITHUB_SHA` | `gh_sha` | Commit SHA that triggered the run |
| `GITHUB_REF_NAME` | `gh_ref_name` | Branch or tag name |
| `GITHUB_WORKFLOW` | `gh_workflow` | Workflow name |
| `GITHUB_JOB` | `gh_job` | Job ID |
| `GITHUB_ACTOR` | `gh_actor` | User or app that triggered the run |
| `GITHUB_REPOSITORY` | `gh_repository` | Owner/repo (e.g. `org/repo`) |
| `GITHUB_RUN_ATTEMPT` | `gh_run_attempt` | Retry attempt number |

If a variable is not set (e.g. running locally), the corresponding field is an empty string.

## Example Workflow

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install pytest-resource-mon

      - run: pytest
        env:
          TINYBIRD_WRITE_TOKEN: ${{ secrets.TINYBIRD_WRITE_TOKEN }}
```

No extra configuration is needed — the `GITHUB_*` variables are set automatically by the Actions runner.
