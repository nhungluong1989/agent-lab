# Deployment Workflow

## Environments

| Environment | Purpose | Branch |
|---|---|---|
| `dev` | Local development & unit tests | feature branches |
| `staging` | Integration testing, pre-release validation | `main` |
| `prod` | Live workloads | tagged release (`v*`) |

- Environment is controlled via the `ENV` environment variable (`dev` / `staging` / `prod`)
- All environment-specific config lives in `conf/<env>.yaml` — no hardcoded values in code
- Secrets are injected via environment variables or Databricks Secrets — never in config files

## Build Procedure

```bash
# 1. Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Lint & format check
ruff check src/
black --check src/

# 4. Run tests with coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# 5. Package for Databricks (wheel or zip)
pip wheel . -w dist/
```

- Build must pass lint, format, and coverage gates before deployment
- Wheel artifacts are uploaded to S3 or DBFS for Databricks job installs

## CI/CD Pipeline

### Trigger rules

| Event | Pipeline |
|---|---|
| Push to feature branch | lint + unit tests |
| PR to `main` | lint + unit tests + integration tests |
| Merge to `main` | deploy to `staging` |
| Tag `v*` pushed | deploy to `prod` |

### Pipeline steps (GitHub Actions example)

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10" }
      - run: pip install -r requirements.txt
      - run: ruff check src/
      - run: black --check src/
      - run: pytest --cov=src --cov-fail-under=80

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - run: ENV=staging python -m src.jobs.deploy

  deploy-prod:
    needs: test
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - run: ENV=prod python -m src.jobs.deploy
```

- Secrets (`DATABRICKS_TOKEN`, `AWS_ACCESS_KEY_ID`, etc.) are injected as GitHub Actions secrets — never stored in YAML
- Integration tests run against `staging` only — never against `prod`

## Deployment Steps

### Databricks ETL jobs

1. Upload wheel artifact to DBFS or S3: `dbfs:/libs/<version>/app.whl`
2. Update Databricks job definition via SDK or Terraform to reference new wheel
3. Trigger a test run on `staging` cluster; verify output row counts and schema
4. Promote to `prod` job after staging validation passes

```python
# deploy script skeleton
from databricks.sdk import WorkspaceClient

def deploy(env: str, wheel_path: str) -> None:
    client = WorkspaceClient()
    job_id = os.environ[f"DATABRICKS_JOB_ID_{env.upper()}"]
    client.jobs.update(job_id, new_settings={"libraries": [{"whl": wheel_path}]})
```

### Streamlit app

```bash
# staging
streamlit run src/app.py --server.port 8501

# prod — run behind a reverse proxy (nginx/ALB) with HTTPS termination
ENV=prod streamlit run src/app.py --server.headless true
```

- Never expose Streamlit directly on port 80/443 — always terminate TLS at the load balancer
- Use `--server.headless true` in all non-local environments

## Environment-Specific Requirements

| Requirement | dev | staging | prod |
|---|---|---|---|
| Databricks cluster | local Spark / Docker | shared interactive | dedicated job cluster |
| Data paths | `s3://bucket/dev/` | `s3://bucket/staging/` | `s3://bucket/prod/` |
| Log level | `DEBUG` | `INFO` | `WARNING` |
| Schema validation | optional | enforced | enforced |
| `.collect()` allowed | yes (tests) | no | no |

## Rollback Strategy

### ETL jobs

1. Identify the last known-good wheel version from the artifact store
2. Re-deploy previous wheel via the deploy script with the old version tag
3. Re-run the affected job partition/date range to reprocess data
4. Quarantine bad output partitions by renaming: `orders/date=2026-04-11` → `orders/_bad/date=2026-04-11`

### Streamlit app

- Keep the previous Docker image or process tagged; restart with the prior version
- Feature flags in `conf/<env>.yaml` can disable a broken feature without redeployment

### Database / Delta table schema changes

- Use additive-only migrations (add columns, never drop or rename in place)
- Test schema evolution on `staging` before applying to `prod`
- Keep a `CHANGELOG.md` entry for every schema change with the affected table and date

## Pre-Deployment Checklist

- [ ] All CI checks pass (lint, format, tests, coverage)
- [ ] No secrets in source code or config files
- [ ] `conf/<env>.yaml` updated for any new config keys
- [ ] Staging deployment validated (row counts, schema, no errors in logs)
- [ ] Rollback path confirmed (previous artifact available)
- [ ] On-call engineer notified for `prod` deployments
