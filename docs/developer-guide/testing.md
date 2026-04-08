# Testing

## Running Tests

Run the full test suite:

```bash
uv run pytest
```

Run with coverage report:

```bash
uv run pytest --cov=dataset_download_tool --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── auth/
│   ├── test_ceda_auth.py       # Token generation and validation
│   ├── test_ftp_auth.py        # FTP authentication
│   └── test_server_status.py   # Server error handling
├── downloader/
│   ├── test_ceda_ftp.py        # FTP download tests
│   ├── test_ceda_http.py       # HTTP download tests
│   └── test_gws_http.py        # GWS HTTP download tests
└── test_s3.py                  # S3 upload tests
```

## Fixtures

All shared fixtures are in `conftest.py`. Key fixtures:

### HTTP Mocking (`pytest-httpserver`)

| Fixture               | Description                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------- |
| `auth_url`            | Mocks the CEDA token creation endpoint. Accepts `status_code` parameter for testing error cases.  |
| `file_url`            | Mocks a file download endpoint. Returns binary data with `application/octet-stream` content type. |
| `file_url_2`          | Second mock file for multi-download tests.                                                        |
| `mock_ceda_directory` | Mocks a CEDA directory listing (JSON response with `items` array).                                |

### GWS Mocking

| Fixture             | Description                                                                         |
| ------------------- | ----------------------------------------------------------------------------------- |
| `file_gws_url`      | Mocks a GWS file download. Sets `GWS_BASE_URL` env var to point to the mock server. |
| `directory_gws_url` | Mocks a GWS directory page (HTML with "Index of" title and file links).             |

### FTP Mocking (`pyftpdlib`)

| Fixture           | Description                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| `mock_ftp_server` | Starts a real FTP server on a random port with `anonymous` user and test files. Yields `(host, port)`. |

### S3 Mocking (`moto`)

| Fixture          | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| `moto_s3_server` | Starts a threaded Moto S3 server with a `testbucket` bucket. |

### Utility

| Fixture         | Description                                                                         |
| --------------- | ----------------------------------------------------------------------------------- |
| `reset_logging` | Auto-use fixture that clears logging handlers after each test to prevent conflicts. |

## Testing Patterns

### Testing a New Download Service

1. Create a mock server fixture in `conftest.py` (or use an existing one)
2. Create a test file in `tests/downloader/`
3. Test at minimum:
   - Single file download
   - Directory download
   - Error handling (auth failure, network error, invalid URL)
   - Checksum verification

Example pattern:

```python
def test_download_file(file_url, tmp_path):
    server = file_url(status_code=200)
    url = server.url_for("/dir/file.nc")

    session = create_session()
    downloader = HTTPDownloader(session=session)
    result = downloader.download(url=url, destination=str(tmp_path))

    assert result.size_bytes > 0
    assert (tmp_path / "file.nc").exists()
```

### Testing Authentication

```python
def test_token_auth(auth_url):
    server = auth_url(status_code=200)
    token_url = server.url_for("/api/token/create/")

    # Patch TOKEN_CREATE_URL to point to mock server
    auth = Auth.from_credentials("user", "pass")
    assert auth.token == "mock-token-abc"
```

### Testing S3 Upload

```python
def test_s3_upload(moto_s3_server):
    # moto_s3_server has a pre-created "testbucket"
    # Set ACCESS_KEY and SECRET_KEY env vars
    # Upload via S3Client and verify
```
