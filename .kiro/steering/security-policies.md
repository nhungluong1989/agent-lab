# Security Policies

## Authentication & Authorization

- Use JWT Bearer tokens for all API authentication (see `api-standards.md`)
- Access tokens must be short-lived (≤ 1 hour); refresh tokens ≤ 30 days
- Never log tokens, passwords, or secrets — mask them as `***` in all log output
- Enforce HTTPS-only; reject plain HTTP connections in production
- Validate token signature, expiry, and issuer on every request — never trust unverified claims
- Apply least-privilege: each service account and API token must have only the permissions it needs
- Rotate Databricks and cloud credentials on a schedule; never embed them in code or notebooks

```python
# ✅ read credentials from environment, never hardcode
import os
token = os.environ["DATABRICKS_TOKEN"]

# ❌ never do this
token = "dapi1234abcd..."
```

## Secrets Management

- Store all secrets in environment variables or a secrets manager (e.g., AWS Secrets Manager, Databricks Secrets)
- `conf/` files must contain only non-sensitive config (paths, app names, feature flags)
- `.env` files are for local dev only — never commit them; ensure `.gitignore` covers `.env`
- CI/CD pipelines must inject secrets via environment variables, not config files

## Data Validation & Input Sanitization

### API layer

- Validate all incoming request bodies against a schema before processing (use `pydantic` or `jsonschema`)
- Reject requests with unexpected or extra fields — do not pass raw user input downstream
- Validate types, ranges, and formats (e.g., email regex, UUID format, date ranges)

```python
# ✅ validate before use
from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    role: str

# ❌ never pass raw dicts from request body directly to DB or Spark
```

### ETL / Spark layer

- Always define explicit `StructType` schemas for external data sources — never use schema inference in production
- Filter and quarantine malformed records before processing; write bad records to a dead-letter path
- Never construct Spark SQL strings from user-supplied input — use the DataFrame API exclusively

```python
# ❌ SQL injection risk
spark.sql(f"SELECT * FROM orders WHERE status = '{user_input}'")

# ✅ parameterised DataFrame API
orders_df.filter(F.col("status") == user_input)
```

## Vulnerability Prevention

### Injection

- No f-string or string-concatenated SQL queries anywhere in `src/`
- Use parameterised queries for any JDBC/database connections
- Sanitize file paths — never pass user-supplied strings directly to `open()`, `os.path`, or Spark read paths

### Dependency Security

- Pin all dependencies with exact versions in `requirements.txt`
- Run `pip audit` or `safety check` in CI to detect known CVEs
- Do not install packages from untrusted or unofficial sources

### Logging & Error Handling

- Never include PII (names, emails, IDs) or secrets in log messages
- Return generic error messages to API clients; log full details server-side only
- Do not expose stack traces in API responses (see `api-standards.md` error format)

```python
# ✅ safe logging
logger.error("Order processing failed", extra={"order_id": order_id, "error_code": e.code})

# ❌ leaks PII and internals
logger.error(f"Failed for user {user.email}: {traceback.format_exc()}")
```

### File & Path Handling

- Validate and allowlist file extensions before reading user-supplied file paths
- Use `pathlib.Path` and resolve paths to prevent directory traversal

```python
from pathlib import Path

def safe_read(base_dir: str, filename: str) -> Path:
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal detected")
    return target
```

## Databricks & Cloud-Specific Rules

- Use Databricks Secrets API (`dbutils.secrets.get`) — never `dbutils.secrets.put` in notebooks committed to source control
- Restrict cluster policies to prevent users from overriding security configs
- Enable audit logging on all Databricks workspaces
- S3/cloud storage buckets must have:
  - Public access blocked
  - Server-side encryption enabled
  - Access restricted to specific IAM roles/service principals

## Secure Coding Checklist

Before merging any PR, verify:

- [ ] No secrets, tokens, or credentials in source code or config files
- [ ] All external inputs validated before use
- [ ] No SQL strings constructed from user input
- [ ] No `.collect()` on unfiltered DataFrames (potential OOM / data leak)
- [ ] Error responses do not expose stack traces or internal paths
- [ ] New dependencies are pinned and scanned for CVEs
- [ ] PII is not written to logs
