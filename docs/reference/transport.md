# Transport Layer

## `Auth`

::: dataset_download_tool.transport.auth.Auth

Manages JWT token-based authentication for CEDA services.

### Constructor

```python
Auth(token: str)
```

Initialize with an existing CEDA access token. Validates JWT format.

**Raises:** `TokenValidationError` if token is empty or invalid.

### Class Methods

#### `Auth.from_credentials(username, password, timeout=30) -> Auth`

Generate a new token from CEDA credentials. Sends a POST request to the CEDA token service with Basic auth.

**Raises:**

- `TokenValidationError` — invalid credentials format
- `AuthError` — token service error or invalid response

### Properties

| Property | Type  | Description                 |
| -------- | ----- | --------------------------- |
| `token`  | `str` | The raw access token string |

### Methods

#### `headers() -> dict[str, str]`

Returns the authorization header: `{"Authorization": "Bearer <token>"}`.

---

## `TokenInfo`

::: dataset_download_tool.transport.auth.TokenInfo

Dataclass holding token data.

| Field          | Type  | Default    | Description                             |
| -------------- | ----- | ---------- | --------------------------------------- |
| `access_token` | `str` | (required) | The JWT access token                    |
| `token_type`   | `str` | `"Bearer"` | Token type for the Authorization header |

Validates that `access_token` is not empty on creation.

---

## `SessionConfig`

::: dataset_download_tool.transport.session.SessionConfig

Dataclass for HTTP session configuration.

| Field            | Type              | Default                     | Description                            |
| ---------------- | ----------------- | --------------------------- | -------------------------------------- |
| `timeout`        | `int`             | `30`                        | Request timeout in seconds             |
| `max_retries`    | `int`             | `3`                         | Maximum retry attempts                 |
| `backoff_factor` | `float`           | `0.5`                       | Exponential backoff multiplier         |
| `retry_statuses` | `tuple[int, ...]` | `(429, 500, 502, 503, 504)` | HTTP status codes that trigger retries |

Validates all numeric fields are positive on creation.

---

## `SessionManager`

::: dataset_download_tool.transport.session.SessionManager

Manages HTTP sessions with automatic retry logic and authentication.

### Constructor

```python
SessionManager(auth: Optional[Auth] = None, config: Optional[SessionConfig] = None)
```

Creates a `requests.Session` with:

- Retry strategy (via `urllib3.util.retry.Retry`)
- HTTP adapter mounted for `http://` and `https://`
- Bearer token headers (if `auth` provided)
- Default timeout applied to all requests

### Properties

| Property  | Type               | Description              |
| --------- | ------------------ | ------------------------ |
| `session` | `requests.Session` | The configured session   |
| `config`  | `SessionConfig`    | The active configuration |

### Methods

#### `update_auth(auth: Auth) -> None`

Updates session authentication headers.

---

## `create_session()`

::: dataset_download_tool.transport.session.create_session

Convenience function that creates a configured `requests.Session`:

```python
session = create_session(timeout=60, auth=auth, max_retries=5)
```

---

## `Client`

::: dataset_download_tool.transport.client.Client

High-level client combining authentication, session management, and downloads.

### Constructor

```python
Client(url, token=None, session=None, timeout=30, max_retries=3)
```

If `token` is provided, creates an authenticated HTTP session. Otherwise uses the provided `session` directly (for FTP/SSH). Calls `get_downloader(url, session)` to select the protocol-specific downloader.

### Class Methods

#### `Client.from_credentials(url, username, password, timeout=30, max_retries=3) -> Client`

Create a client by generating a CEDA token from credentials.

#### `Client.ssh_client(url, hostname, username, key_filename) -> Client`

Create a client with SSH key authentication via `paramiko.SSHClient`.

**Raises:** `AuthError` if SSH connection fails.

#### `Client.ftp_login(url, username, password) -> Client`

Create a client with FTP login.

**Raises:**

- `ValidationError` — invalid FTP URL
- `AuthError` — FTP login failure

### Methods

#### `download(url, destination=None, show_progress=True, calculate_checksum=False) -> DownloadResult`

Download a file or directory. Sets up a progress bar (unless disabled) and delegates to the selected downloader.

#### `validate_url(url) -> str` (static)

Validates URL scheme (`http`, `https`, `ftp`) and structure.

**Raises:** `ValidationError` for invalid URLs.
