# Design

This document describes the detailed design of the Dataset Download Tool — the
classes that make up the implementation, the design patterns they use, and the
runtime interactions between them. For a higher-level view of the system, see
[Architecture](architecture.md).

## Class Diagram

The class diagram below shows the main classes in the tool and their
relationships. The `BaseDownloader` abstract class is at the heart of the
downloader layer — concrete downloaders (`HTTPDownloader`, `FTPDownloader`,
`SSHDownloader`, `HTTPDownloaderGWS`) implement the protocol-specific behaviour.

```mermaid
classDiagram
    class ConfigLoader {
        -parser: ArgumentParser
        +parse(argv) Namespace
        -_build_parser() ArgumentParser
        -_load_config_file(path) dict
        -_merge(cli_args, file_data) Namespace
        -_validate(config) None
    }

    class Auth {
        -_token_info: TokenInfo
        +__init__(token)
        +from_credentials(username, password, timeout)$ Auth
        +token: str
        +headers() dict
    }

    class TokenInfo {
        +access_token: str
        +token_type: str
    }

    class SessionConfig {
        +timeout: int
        +max_retries: int
        +backoff_factor: float
        +retry_statuses: tuple
    }

    class SessionManager {
        -_config: SessionConfig
        -_auth: Auth
        -_session: Session
        +session: Session
        +config: SessionConfig
        +update_auth(auth)
    }

    class Client {
        -_token: str
        -_session: Session | FTP | SSHClient
        -_downloader: BaseDownloader
        +__init__(url, token, session, timeout, max_retries)
        +from_credentials(url, username, password)$ Client
        +ssh_client(url, hostname, username, key_filename)$ Client
        +ftp_login(url, username, password)$ Client
        +download(url, destination, show_progress, calculate_checksum) DownloadResult
        +validate_url(url)$ str
    }

    class BaseDownloader {
        <<abstract>>
        #_chunk_size: int
        #_session: Session | FTP | SSHClient
        +download(url, destination, progress_callback, calculate_checksum) DownloadResult
        #_stream(url)* tuple
        #_is_directory(url)* bool
        #_recursive_download(url, dest, checksum, callback)* list~DownloadResult~
        #_write_file(...) DownloadResult
        +s3_upload(...) DownloadResult
    }

    class HTTPDownloader {
        +_stream(url) tuple
        +_is_directory(url) bool
        +_recursive_download(...) list~DownloadResult~
        -_directory_contents(url) dict
    }

    class HTTPDownloaderGWS {
        +_is_directory(url) bool
        +_directory_contents(url) dict
        +_recursive_download(...) list~DownloadResult~
        -_get_soup(url) BeautifulSoup
    }

    class FTPDownloader {
        +_stream(url) tuple
        +_is_directory(url) bool
        +_recursive_download(...) list~DownloadResult~
        -_get_directory_contents(url) dict
    }

    class SSHDownloader {
        -_sftp: SFTPClient
        +_stream(path) tuple
        +_is_directory(path) bool
        +_recursive_download(...) list~DownloadResult~
        -_directory_contents(path) list
    }

    class DownloadResult {
        +url: str | list
        +destination: Path | list
        +size_bytes: int
        +checksum: str | None
        +size_mb: float
    }

    class S3Client {
        -_client: boto3.S3Client
        +CHUNK_SIZE: int
        +upload_to_s3(chunk_iter, bucket, key, ...) dict
        -_upload_part(...) str
    }

    Auth --> TokenInfo : contains
    SessionManager --> Auth : uses
    SessionManager --> SessionConfig : uses
    Client --> SessionManager : creates session via
    Client --> BaseDownloader : delegates to
    BaseDownloader <|-- HTTPDownloader
    BaseDownloader <|-- FTPDownloader
    BaseDownloader <|-- SSHDownloader
    HTTPDownloader <|-- HTTPDownloaderGWS
    BaseDownloader --> DownloadResult : returns
    BaseDownloader --> S3Client : uses for S3 uploads
```

## Design Patterns

### Factory Pattern — `get_downloader()`

The `get_downloader()` function in `downloader/__init__.py` selects the appropriate downloader based on URL prefix:

| URL Pattern | Downloader |
|-------------|------------|
| Starts with `GWS_BASE_URL` | `HTTPDownloaderGWS` |
| `http://` or `https://` | `HTTPDownloader` |
| `ftp://` | `FTPDownloader` |
| Anything else (file paths) | `SSHDownloader` |

### Template Method — `BaseDownloader.download()`

`BaseDownloader` defines the download algorithm in `download()`. Subclasses provide the protocol-specific behaviour by implementing three abstract methods:

- `_stream(url)` — return an iterable of bytes and optional total size
- `_is_directory(url)` — check whether the URL points to a directory
- `_recursive_download(...)` — handle directory traversal

### Alternative Constructors — `Client`

`Client` uses class methods as alternative constructors for different authentication modes:

- `Client(url, token=...)` — direct token
- `Client.from_credentials(url, username, password)` — generate token from CEDA credentials
- `Client.ssh_client(url, hostname, username, key_filename)` — SSH key auth
- `Client.ftp_login(url, username, password)` — FTP login

## Sequence Diagrams

The following sequence diagrams show the runtime interactions for the main
use-cases: command-line execution, authentication, and the download process
itself.

### CLI Execution Flow

This diagram traces a full invocation of the CLI from argument parsing through
to the final download result.

```mermaid
sequenceDiagram
    participant User
    participant main as main()
    participant CL as ConfigLoader
    participant Client
    participant GD as get_downloader()
    participant BD as BaseDownloader

    User->>main: dataset-download-tool [args]
    main->>CL: ConfigLoader().parse()
    CL->>CL: _build_parser() + parse_args()
    alt --config provided
        CL->>CL: _load_config_file()
        CL->>CL: _merge(cli_args, file_data)
    end
    CL->>CL: _validate()
    CL-->>main: args (Namespace)
    main->>main: setup_logging()

    alt SSH mode
        main->>Client: Client.ssh_client(...)
    else Token
        main->>Client: Client(url, token)
    else Credentials
        main->>Client: Client.from_credentials(...)
    else FTP
        main->>Client: Client.ftp_login(...)
    else No auth
        main->>Client: Client(url, "no_auth")
    end

    Client->>GD: get_downloader(url, session)
    GD-->>Client: downloader instance

    main->>Client: client.download(url, dest, ...)
    Client->>BD: downloader.download(url, dest, ...)
    BD-->>Client: DownloadResult
    Client-->>main: DownloadResult
    main->>User: print success
```

### Authentication Flow

Authentication can happen in two ways — a pre-existing token can be passed
directly, or CEDA credentials can be exchanged for a token via the CEDA token
service.

```mermaid
sequenceDiagram
    participant Client
    participant Auth
    participant CEDA as CEDA Token Service

    alt Direct token
        Client->>Auth: Auth(token)
        Auth->>Auth: _validate_token()
        Auth-->>Client: Auth instance
    else From credentials
        Client->>Auth: Auth.from_credentials(user, pass)
        Auth->>Auth: _validate_credentials()
        Auth->>CEDA: POST /api/token/create/ (Basic auth)
        CEDA-->>Auth: {"access_token": "..."}
        Auth->>Auth: Auth(token)
        Auth-->>Client: Auth instance
    end

    Client->>Client: create_session(auth)
    Note over Client: Session headers include<br/>Authorization: Bearer token
```

### Download Flow

The download flow shows how the `BaseDownloader.download()` template method
orchestrates single-file, directory, and multi-URL downloads — and how
destinations can be either local paths or an S3 bucket.

```mermaid
sequenceDiagram
    participant Client
    participant PL as ProgressLogger
    participant BD as BaseDownloader
    participant WF as _write_file()
    participant S3 as S3Client

    Client->>PL: create_progress_bar()
    PL-->>Client: (progress_callback, close_fn)
    Client->>BD: download(url, dest, callback, checksum)
    BD->>BD: multiple_urls_split(url)

    alt Single URL
        BD->>BD: resolve_destination(url, dest)
        alt Directory
            BD->>BD: _recursive_download()
            Note over BD: Downloads each file recursively
        else File
            BD->>BD: _stream(url) → (chunks, size)
            alt Local destination (Path)
                BD->>WF: _write_file(url, dest, chunks, ...)
                WF->>WF: Write chunks + MD5 + progress
                WF-->>BD: DownloadResult
            else S3 destination (dict)
                BD->>S3: s3_upload(url, chunks, dest, ...)
                S3->>S3: Multipart upload
                S3-->>BD: DownloadResult
            end
        end
    else Multiple URLs (pipe-separated)
        BD->>BD: multiple_url_download()
        Note over BD: Loop: get_downloader + download each
        BD->>BD: multiple_download_result()
    end

    BD-->>Client: DownloadResult
    Client->>PL: close_fn()
```
