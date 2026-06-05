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

| Field         | Type                 | Description                                    |
| ------------- | -------------------- | ---------------------------------------------- |
| `url`         | `str \| list[str]`   | Source URL(s)                                  |
| `destination` | `Path \| str \| list` | Local path or remote URL where files were saved |
| `size_bytes`  | `int`                | Total downloaded bytes                         |
| `checksum`    | `Optional[str]`      | MD5 hash (if requested)                        |

**Properties:**

- `size_mb -> float` — size converted to MiB

### `ProgressCallback`

Type alias: `Callable[[int, int], None]` — callback receiving `(bytes_downloaded, total_bytes)`.

---

## `BaseDownloader`

::: dataset_download_tool.downloader.base.BaseDownloader

Abstract base class for all protocol-specific downloaders.

### Abstract Methods

| Method                | Signature                                                          | Description                                           |
| --------------------- | ------------------------------------------------------------------ | ----------------------------------------------------- |
| `_stream`             | `(url) -> tuple[Iterable[bytes], Optional[int]]`                   | Stream data as chunks; return iterator and total size |
| `_is_directory`       | `(url) -> bool`                                                    | Check if URL points to a directory                    |
| `_recursive_download` | `(url, dest, checksum, callback, storage) -> list[DownloadResult]` | Download all files in a directory                     |

### Concrete Methods

#### `download(url, destination=None, progress_callback=None, calculate_checksum=False, storage="local") -> DownloadResult`

Main download orchestration:

1. Split pipe-separated URLs (`multiple_urls_split`)
2. Resolve destination path (`resolve_destination` from `storage_selector/selector_utils.py`)
3. Check if directory → `_recursive_download(..., storage)`
4. Stream file → `_write_file()` (local) or `remote_path_upload()` (S3 / Azure Blob)

The `storage` parameter is a string: `"local"` (default), `"s3"`, or `"blob"`.

#### `_write_file(url, dest_path, chunk_iter, total_size, progress_callback, calculate_checksum) -> DownloadResult`

Writes chunks to a local file. Optionally computes MD5 hash and reports progress.

#### `remote_path_upload(url, chunk_iter, dest_path, calculate_checksum, progress_callback, total_size, storage) -> DownloadResult`

Uploads chunks to a remote storage backend via `get_uploader()`. Handles both S3
multipart uploads and Azure Blob block uploads depending on `storage`.

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

## Storage Selector

The `storage_selector` package abstracts where downloaded data is written. It is
selected at runtime via the `storage` parameter (`"local"`, `"s3"`, or `"blob"`).

### `get_uploader()`

::: dataset_download_tool.storage_selector.get_uploader

Factory that returns the appropriate uploader for the given storage backend:

| `storage` value | Returns           | Backend                       |
| --------------- | ----------------- | ----------------------------- |
| `"s3"`          | `S3Client`        | S3-compatible object storage  |
| `"blob"`        | `AzureBlobClient` | Azure Blob Storage            |

### `BaseUploader`

::: dataset_download_tool.storage_selector.base.BaseUploader

Abstract base class for all storage uploaders. Defines the common interface:

#### `upload(chunk_iter, bucket, key, total_size=0, calculate_checksum=False, progress_callback=None) -> dict`

Upload a stream of byte chunks to the given container/bucket and key. Returns a
`dict` with `destination`, `size_bytes`, and `checksum`.

### `S3Client`

::: dataset_download_tool.storage_selector.s3_upload.S3Client

S3 multipart upload client using `boto3`. Inherits from `BaseUploader`.

#### Constructor

```python
S3Client(s3_endpoint: str)
```

Creates a `boto3` S3 client connected to the given endpoint. Reads credentials
from the `ACCESS_KEY` and `SECRET_KEY` environment variables.

#### Methods

##### `upload(chunk_iter, bucket, key, total_size=0, calculate_checksum=False, progress_callback=None) -> dict`

Performs S3 multipart upload:

1. `create_multipart_upload()`
2. For each 5 MiB buffer: `_upload_part()`
3. `complete_multipart_upload()`

Aborts the upload and raises on error. Returns `dict` with `destination`,
`size_bytes`, and `checksum`.

#### Constants

- `CHUNK_SIZE` — `5 * 1024 * 1024` (5 MiB per part)

### `AzureBlobClient`

::: dataset_download_tool.storage_selector.azure_upload.AzureBlobClient

Azure Blob Storage block-upload client using `azure-storage-blob`. Inherits from `BaseUploader`.

#### Constructor

```python
AzureBlobClient(blob_url: str)
```

Creates a `BlobServiceClient` using `AZURE_STORAGE_ACCOUNT_NAME` and
`AZURE_STORAGE_KEY` environment variables.

**Raises:** `ValidationError` if the endpoint URL is invalid.

#### Methods

##### `upload(chunk_iter, bucket, key, total_size=0, calculate_checksum=False, progress_callback=None) -> dict`

Performs Azure block upload:

1. For each 4 MiB buffer: `_stage_block()` (returns a block ID)
2. `commit_block_list()`

Cleans up uncommitted blocks on error and raises. Returns `dict` with
`destination`, `size_bytes`, and `checksum`.

#### Constants

- `CHUNK_SIZE` — `4 * 1024 * 1024` (4 MiB per block)

---

## Utility Functions

### `resolve_destination(url, destination, storage) -> Path | dict`

::: dataset_download_tool.storage_selector.selector_utils.resolve_destination

Resolves the download destination based on the active storage backend:

| `storage` | Destination input | Result |
|-----------|-------------------|--------|
| `"local"` | `None` | `cwd / filename` |
| `"local"` | Directory path | `directory / filename` |
| `"local"` | File path | used as-is |
| `"s3"` | `https://[bucket].[endpoint]/dir` | `{"endpoint", "bucket", "key"}` |
| `"s3"` | `s3://...` | raises `ValidationError` (wrong format) |
| `"blob"` | `http(s)://[container].[host]/account/dir` | `{"endpoint", "bucket", "key"}` |
| `"blob"` | other | raises `ValidationError` |

### `extract_filename(url) -> str`

::: dataset_download_tool.downloader.download_utils.extract_filename

Extracts the filename from a URL path (e.g., `https://example.com/dir/file.nc` → `file.nc`).

### `multiple_urls_split(url) -> list[str] | str`

::: dataset_download_tool.downloader.download_utils.multiple_urls_split

Splits pipe-separated URLs into a list. Returns a single string if only one URL.

### `multiple_url_download(url, destination, ...) -> list[DownloadResult]`

::: dataset_download_tool.downloader.download_utils.multiple_url_download

Downloads each URL in the list using `get_downloader()` for each.

### `multiple_download_result(url, results) -> DownloadResult`

::: dataset_download_tool.downloader.download_utils.multiple_download_result

Aggregates a list of `DownloadResult` into a single result with combined destinations and total size.

---

## `ProgressLogger`

::: dataset_download_tool.downloader.progress_logger.ProgressLogger

### Static Methods

#### `create_progress_logger(log_interval_mb=10) -> ProgressCallback`

Creates a logging-based progress callback that logs every `log_interval_mb` MiB.

#### `create_progress_bar(desc="Downloading") -> tuple[ProgressCallback, Callable[[], None]]`

Creates a console progress bar. Returns `(progress_callback, close_function)`.
