# API Standards

## REST Conventions

- Use **nouns** for resources, not verbs
- Use **plural** resource names: `/users`, `/orders`
- Nest related resources up to 2 levels: `/users/{id}/orders`
- Use **kebab-case** for multi-word paths: `/user-profiles`
- Query params for filtering, sorting, pagination: `?status=active&sort=created_at&page=1&limit=20`

## Endpoint Naming Patterns

| Action | Method | Path |
|---|---|---|
| List | GET | `/resources` |
| Get one | GET | `/resources/{id}` |
| Create | POST | `/resources` |
| Full update | PUT | `/resources/{id}` |
| Partial update | PATCH | `/resources/{id}` |
| Delete | DELETE | `/resources/{id}` |

## Versioning

- Version via URL prefix: `/v1/users`, `/v2/users`
- Increment major version on breaking changes only
- Support previous major version for minimum 6 months after deprecation notice
- Include `Deprecation` and `Sunset` headers on deprecated endpoints

```
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
```

## Authentication

### Bearer Token (JWT)

```
Authorization: Bearer <token>
```

### Flow

1. Client POSTs credentials to `/v1/auth/token`
2. Server returns `access_token` (short-lived) + `refresh_token` (long-lived)
3. Client uses `access_token` in `Authorization` header
4. On 401, client POSTs `refresh_token` to `/v1/auth/refresh` for new tokens
5. On refresh failure, redirect to login

### Token Endpoint Examples

**Login**
```http
POST /v1/auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret"
}
```

```json
{
  "access_token": "eyJ...",
  "refresh_token": "dGh...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Refresh**
```http
POST /v1/auth/refresh
Content-Type: application/json

{ "refresh_token": "dGh..." }
```

## HTTP Status Codes

| Code | When to use |
|---|---|
| 200 | Successful GET, PUT, PATCH |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE (no body) |
| 400 | Validation / malformed request |
| 401 | Missing or invalid auth token |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate) |
| 422 | Unprocessable entity (semantic errors) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Error Response Format

All errors return a consistent JSON body:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2026-04-11T13:00:00Z"
  }
}
```

- `code`: machine-readable string constant (SCREAMING_SNAKE_CASE)
- `message`: human-readable summary
- `details`: optional array for field-level errors
- `request_id`: trace ID for debugging (always include)
- `timestamp`: ISO 8601 UTC

## Request / Response Examples

**Create a user**
```http
POST /v1/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "role": "editor"
}
```

```http
HTTP/1.1 201 Created
Location: /v1/users/usr_789

{
  "id": "usr_789",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "role": "editor",
  "created_at": "2026-04-11T13:00:00Z"
}
```

**List with pagination**
```http
GET /v1/users?page=2&limit=10&sort=created_at&order=desc
Authorization: Bearer <token>
```

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 10,
    "total": 95,
    "total_pages": 10
  }
}
```

## General Rules

- Always return `Content-Type: application/json`
- Use ISO 8601 for all timestamps (`2026-04-11T13:00:00Z`)
- Use `snake_case` for all JSON field names
- Never expose internal stack traces in error responses
- Include `X-Request-ID` in every response header
