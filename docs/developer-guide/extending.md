# Extending the Tool

This guide covers how to add new download protocols, destination types, and custom exceptions.

## Adding a New Download Service

The downloader layer uses a template method pattern. To add a new protocol, you subclass `BaseDownloader` and implement three abstract methods, then register it in the factory.

### Step 1: Create the Service

Create a new file in `dataset_download_tool/downloader/services/`, e.g. `new_protocol_service.py`:

```python
from typing import Optional
from dataset_download_tool.downloader.base import BaseDownloader
from dataset_download_tool.downloader.models import DownloadResult, ProgressCallback


class NewProtocolDownloader(BaseDownloader):
    """Downloader implementation for <your protocol>."""

    def __init__(self, session):
        # session is whatever client object your protocol needs
        super().__init__(session)

    def _stream(self, url: str) -> tuple:
        """Stream data from the source.

        Must return a tuple of:
          - An iterable of bytes (chunk generator)
          - Optional total size in bytes (int or None)
        """
        # Connect to your protocol and yield chunks
        total_size = ...  # or None if unknown
        def chunk_generator():
            while data := read_chunk(self._chunk_size):
                yield data
        return chunk_generator(), total_size

    def _is_directory(self, url: str) -> bool:
        """Check if the URL points to a directory."""
        ...

    def _recursive_download(
        self,
        url: str,
        destination,
        calculate_checksum: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> list[DownloadResult]:
        """Download all files in a directory."""
        results = []
        for file_url in self._list_directory(url):
            result = self.download(
                url=file_url,
                destination=f"{destination}/{filename}",
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            results.append(result)
        return results
```

The inherited methods handle everything else:

- `download()` — orchestrates single/multiple/directory downloads
- `_write_file()` — writes chunks to a local file with optional MD5 and progress
- `s3_upload()` — streams chunks to S3 via multipart upload

### Step 2: Register in the Factory

Edit `dataset_download_tool/downloader/__init__.py` and add your protocol to `get_downloader()`:

```python
from dataset_download_tool.downloader.services.new_protocol_service import NewProtocolDownloader

def get_downloader(url: str, session=None):
    if url.startswith("newproto://"):
        return NewProtocolDownloader(session=session)
    elif url.startswith(GWS_HOST):
        return HTTPDownloaderGWS(session=session)
    # ... existing cases
```

### Step 3: Add a Client Constructor (if needed)

If your protocol requires special session setup, add a class method to `Client` in `transport/client.py`:

```python
@classmethod
def new_protocol_client(cls, url, **kwargs) -> "Client":
    session = create_new_protocol_session(**kwargs)
    return cls(url=url, session=session)
```

### Step 4: Wire into the CLI

Add the new auth/protocol option to `cli/config_parser.py` (in the mutually exclusive auth group) and handle it in `cli/main.py`:

```python
# In main():
if args.new_protocol:
    client = Client.new_protocol_client(url=args.url, ...)
```

### Step 5: Write Tests

Follow existing patterns in `tests/`. Key fixtures from `conftest.py`:

- `httpserver` — mock HTTP server (via `pytest-httpserver`)
- `mock_ftp_server` — mock FTP server (via `pyftpdlib`)
- `moto_s3_server` — mock S3 (via `moto`)

## Concrete Example: FTPDownloader

The `FTPDownloader` in `downloader/services/ftp_service.py` is a good reference:

- **`__init__`**: calls `super().__init__(session)` with an `ftplib.FTP` session
- **`_stream`**: uses `retrbinary()` with a callback queue (`deque`) to produce a chunk generator
- **`_is_directory`**: attempts `cwd()` on the path — success means directory
- **`_recursive_download`**: lists files with `nlst()`, downloads each recursively

## Adding a New Destination Type

The download destination is resolved by `resolve_destination()` in `downloader/download_utils.py`:

- Returns a `Path` for local filesystem destinations
- Returns a `dict` with `endpoint`, `bucket`, `key` for S3 destinations

`BaseDownloader.download()` dispatches based on the return type:

```python
if isinstance(dest_path, Path):
    return self._write_file(...)
if isinstance(dest_path, dict):
    return self.s3_upload(...)
```

To add a new destination type:

1. Extend `resolve_destination()` to detect and parse the new destination format
2. Return a distinguishable type (e.g., a new dataclass)
3. Add a corresponding branch in `BaseDownloader.download()`
4. Implement the upload/write logic

## Adding Custom Exceptions

All project exceptions inherit from `DFTError` in `exceptions.py`:

```
DFTError
├── AuthError
│   └── TokenValidationError
├── DownloadError
│   └── ValidationError
└── BucketNotFoundError
```

To add a new exception:

```python
class NewProtocolError(DownloadError):
    """Raised when the new protocol encounters an error."""
    pass
```

Then handle it in `cli/main.py`:

```python
except NewProtocolError as e:
    logger.error(f"new protocol failed: {e}")
    sys.exit(1)
```
