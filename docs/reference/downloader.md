# Downloader

## `get_downloader()`

::: dataset_download_tool.downloader.get_downloader

Factory function that returns the appropriate downloader based on URL protocol:

| URL Pattern                        | Returns             |
| ---------------------------------- | ------------------- |
| Starts with `GWS_BASE_URL` env var | `HTTPDownloaderGWS` |
| `http://` or `https://`            | `HTTPDownloader`    |
| `ftp://`                           | `FTPDownloader`     |
| Anything else (file paths)         | `SSHDownloader`     |

---

## `DownloadResult`

::: dataset_download_tool.downloader.models.DownloadResult

Dataclass representing download metadata.

| Field         | Type                 | Description                          |
| ------------- | -------------------- | ------------------------------------ |
| `url`         | `str \| list[str]`   | Source URL(s)                        |
| `destination` | `Path \| list[Path]` | Local path(s) where files were saved |
| `size_bytes`  | `int`                | Total downloaded bytes               |
| `checksum`    | `Optional[str]`      | MD5 hash (if requested)              |

**Properties:**

- `size_mb -> float` — size converted to MiB

### `ProgressCallback`

Type alias: `Callable[[int, int], None]` — callback receiving `(bytes_downloaded, total_bytes)`.

---

## `BaseDownloader`

::: dataset_download_tool.downloader.base.BaseDownloader

Abstract base class for all protocol-specific downloaders.

### Abstract Methods

| Method                | Signature                                                 | Description                                           |
| --------------------- | --------------------------------------------------------- | ----------------------------------------------------- |
| `_stream`             | `(url) -> tuple[Iterable[bytes], Optional[int]]`          | Stream data as chunks; return iterator and total size |
| `_is_directory`       | `(url) -> bool`                                           | Check if URL points to a directory                    |
| `_recursive_download` | `(url, dest, checksum, callback) -> list[DownloadResult]` | Download all files in a directory                     |

### Concrete Methods

#### `download(url, destination=None, progress_callback=None, calculate_checksum=False) -> DownloadResult`

Main download orchestration:

1. Split pipe-separated URLs (`multiple_urls_split`)
2. Resolve destination path (`resolve_destination`)
3. Check if directory → `_recursive_download()`
4. Stream file → `_write_file()` (local) or `s3_upload()` (S3)

#### `_write_file(url, dest_path, chunk_iter, total_size, progress_callback, calculate_checksum) -> DownloadResult`

Writes chunks to a local file. Optionally computes MD5 hash and reports progress.

#### `s3_upload(url, chunk_iter, dest_path, calculate_checksum, progress_callback, total_size) -> DownloadResult`

Streams chunks to S3 via `S3Client` multipart upload.

### Class Constants

- `DEFAULT_CHUNK_SIZE` — from `DEFAULT_CHUNK_SIZE` env var (default: `8192`)

---

## Service Implementations

### `HTTPDownloader`

::: dataset_download_tool.downloader.services.http_service.HTTPDownloader

HTTP/HTTPS downloader using `requests.Session`.

- **`_stream(url)`** — `session.get()` with streaming; yields chunks from response
- **`_is_directory(url)`** — checks if response content type is JSON (CEDA directory listing)
- **`_recursive_download()`** — fetches JSON directory, downloads each item
- Converts `dap.ceda.ac.uk` URLs to `data.ceda.ac.uk` for JSON API queries

### `HTTPDownloaderGWS`

::: dataset_download_tool.downloader.services.http_gws.HTTPDownloaderGWS

GWS-specific HTTP downloader. Extends `HTTPDownloader` with HTML-based directory detection:

- **`_is_directory(url)`** — checks if HTML `<title>` starts with "Index of"
- **`_directory_contents(url)`** — parses HTML with BeautifulSoup, extracts `<a>` links
- **`_recursive_download()`** — downloads all linked files from the HTML listing

### `FTPDownloader`

::: dataset_download_tool.downloader.services.ftp_service.FTPDownloader

FTP downloader using `ftplib.FTP`.

- **`_stream(url)`** — uses `retrbinary()` with a callback queue (`deque`) to produce a chunk generator
- **`_is_directory(url)`** — attempts `cwd()` on the path; success means directory
- **`_recursive_download()`** — lists files with `nlst()`, downloads each

### `SSHDownloader`

::: dataset_download_tool.downloader.services.ssh_service.SSHDownloader

SSH/SFTP downloader using `paramiko.SSHClient`.

- Opens an SFTP session on initialization (`self._sftp`)
- **`_stream(path)`** — opens remote file with `prefetch()` for efficient reads
- **`_is_directory(path)`** — checks `stat().st_mode` via SFTP
- **`_recursive_download()`** — lists directory with `listdir()`, downloads each file

---

## `S3Client`

::: dataset_download_tool.downloader.s3_upload.S3Client

S3 multipart upload client using `boto3`.

### Constructor

```python
S3Client(s3_endpoint: str)
```

Creates a `boto3` S3 client connected to the given endpoint. Uses `ACCESS_KEY` and `SECRET_KEY` environment variables.

### Methods

#### `upload_to_s3(chunk_iter, bucket, key, total_size, calculate_checksum, progress_callback) -> dict`

Performs multipart upload:

1. `create_multipart_upload()`
2. For each 5 MiB chunk: `_upload_part()`
3. `complete_multipart_upload()`

Returns `dict` with `destination`, `size_bytes`, and `checksum`.

### Constants

- `CHUNK_SIZE` — `5 * 1024 * 1024` (5 MiB per part)

---

## Utility Functions

::: dataset_download_tool.downloader.download_utils

### `extract_filename(url) -> str`

Extracts the filename from a URL path (e.g., `https://example.com/dir/file.nc` → `file.nc`).

### `resolve_destination(url, destination) -> Path | dict`

Resolves the download destination:

- `None` → current directory + extracted filename
- Directory path → directory + extracted filename
- File path → used as-is
- `https://` URL → parsed as S3 destination (`{"endpoint", "bucket", "key"}`)
- `s3://` → raises `ValidationError` (wrong format)

### `multiple_urls_split(url) -> list[str] | str`

Splits pipe-separated URLs into a list. Returns a single string if only one URL.

### `multiple_url_download(url, destination, ...) -> list[DownloadResult]`

Downloads each URL in the list using `get_downloader()` for each.

### `multiple_download_result(url, results) -> DownloadResult`

Aggregates a list of `DownloadResult` into a single result with combined destinations and total size.

---

## `ProgressLogger`

::: dataset_download_tool.downloader.progress_logger.ProgressLogger

### Static Methods

#### `create_progress_logger(log_interval_mb=10) -> ProgressCallback`

Creates a logging-based progress callback that logs every `log_interval_mb` MiB.

#### `create_progress_bar(desc="Downloading") -> tuple[ProgressCallback, Callable[[], None]]`

Creates a console progress bar. Returns `(progress_callback, close_function)`.
