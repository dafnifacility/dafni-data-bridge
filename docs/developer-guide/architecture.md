# Architecture

This document gives a high-level view of how the Dataset Download Tool is
organised and how its layers interact. For the detailed class model, design
patterns, and runtime sequence diagrams, see [Design](design.md).

## Layers

The codebase is organized into three layers:

| Layer          | Package       | Responsibility                                                   |
| -------------- | ------------- | ---------------------------------------------------------------- |
| **CLI**        | `cli/`        | Argument parsing, config file loading, entry point orchestration |
| **Transport**  | `transport/`  | Authentication, HTTP session management, client construction     |
| **Downloader** | `downloader/` | Protocol-specific file downloads, S3 upload, progress tracking   |

## Software Architecture Diagram

The diagram below shows the major components of the tool, how they are grouped
into layers, and how they interact with external systems (the user, remote
dataset servers, the CEDA token service, and S3-compatible object storage).

```mermaid
flowchart TB
    User([User / DAFNI Model])
    ConfigFile[/JSON config file/]

    subgraph CLI["CLI Layer (cli/)"]
        Main["main.py<br/>Entry point"]
        ConfigLoader["config_parser.py<br/>ConfigLoader"]
    end

    subgraph Transport["Transport Layer (transport/)"]
        Client["client.py<br/>Client"]
        Auth["auth.py<br/>Auth"]
        Session["session.py<br/>SessionManager"]
    end

    subgraph Downloader["Downloader Layer (downloader/)"]
        Factory["__init__.py<br/>get_downloader()"]
        Base["base.py<br/>BaseDownloader"]

        subgraph Services["services/"]
            HTTP["HTTPDownloader"]
            GWS["HTTPDownloaderGWS"]
            FTP["FTPDownloader"]
            SSH["SSHDownloader"]
        end

        Progress["progress_logger.py"]
        S3Up["s3_upload.py<br/>S3Client"]
    end

    subgraph External["External Systems"]
        CEDA[("CEDA Token<br/>Service")]
        HTTPSrv[("HTTP/HTTPS<br/>Servers")]
        FTPSrv[("FTP Servers")]
        SSHSrv[("SSH/SFTP<br/>Servers")]
        S3[("S3-compatible<br/>Object Storage")]
    end

    User -->|command-line args| Main
    ConfigFile -.->|--config| ConfigLoader
    Main --> ConfigLoader
    Main --> Client

    Client --> Auth
    Client --> Session
    Client --> Factory
    Factory -->|selects by URL| Services
    Services -.->|inherits| Base

    Auth -->|POST /api/token/create/| CEDA
    Session -.->|HTTP with retry| HTTPSrv

    HTTP --> HTTPSrv
    GWS --> HTTPSrv
    FTP --> FTPSrv
    SSH --> SSHSrv

    Base --> Progress
    Base --> S3Up
    S3Up --> S3

    classDef layer fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef actor fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    class CLI,Transport,Downloader,Services layer
    class CEDA,HTTPSrv,FTPSrv,SSHSrv,S3 external
    class User,ConfigFile actor
```

The `main()` entry point in the CLI layer delegates argument handling to
`ConfigLoader`, then constructs a `Client` in the transport layer. The
`Client` sets up authentication and an HTTP session (with retry logic) and
uses the `get_downloader()` factory to pick a concrete downloader from the
downloader layer based on the URL protocol. Each concrete downloader talks
to its own external protocol endpoint, and destination writes can go either
to the local filesystem or — via `S3Client` — to an S3-compatible bucket.

## Data Flow Summary

The diagram below traces the main function calls made during a single
invocation of the tool, from `main()` through to the final `DownloadResult`.
Each node is labelled with the function or class responsible for that step.

```mermaid
flowchart TD
    Start(["main()"]) --> Parse["ConfigLoader.parse()<br/><i>Parse CLI args + optional JSON config</i>"]
    Parse --> ClientCtor{"Client constructor"}

    ClientCtor -->|token| CI1["Client.__init__()"]
    ClientCtor -->|credentials| CI2["Client.from_credentials()"]
    ClientCtor -->|SSH key| CI3["Client.ssh_client()"]
    ClientCtor -->|FTP login| CI4["Client.ftp_login()"]

    CI1 --> Setup["Auth + SessionManager<br/><i>Token validation + HTTP retry session</i>"]
    CI2 --> Setup
    CI3 --> Setup
    CI4 --> Setup

    Setup --> Factory["get_downloader(url, session)<br/><i>Factory: pick downloader by URL</i>"]
    Factory --> Dl["Client.download()"]

    Dl --> PL["ProgressLogger<br/><i>Set up progress bar</i>"]
    PL --> BD["BaseDownloader.download()<br/><i>Template method</i>"]

    BD --> DecDir{"Directory?"}
    DecDir -->|yes| Rec["_recursive_download()<br/><i>Directory traversal</i>"]
    DecDir -->|no| Stream["_stream()"]

    Stream --> DecDest{"Destination?"}
    DecDest -->|local path| WF["_write_file()<br/><i>Single file to local disk</i>"]
    DecDest -->|S3 bucket| S3["s3_upload()<br/><i>Single file to S3</i>"]

    Rec --> Result["DownloadResult<br/><i>url, destination, size, checksum</i>"]
    WF --> Result
    S3 --> Result
    Result --> End([return to user])

    classDef entry fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef result fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    class Start,End entry
    class ClientCtor,DecDir,DecDest decision
    class Result result
```

For the detailed class model and runtime sequence diagrams, see
[Design](design.md).
