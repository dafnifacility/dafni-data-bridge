# Dataset Download Tool

A unified interface for downloading files from SSH, HTTP, and FTP servers, including CEDA and JASMIN GWS, with support for saving to local disk or S3-compatible buckets.

## Features

### Protocol & Authentication Matrix

| Source Protocol | Authentication Options | Destination Options | Additional Capabilities |
|----------------|----------------------|-------------------|------------------------|
| **HTTP/HTTPS** | • CEDA token<br>• Username/password<br>• No-auth (public files) | • Local filesystem<br>• S3-compatible buckets | • MD5 checksum verification<br>• Batch downloads (pipe-separated URLs)<br>• Directory downloads (recursive) |
| **FTP** | • Username/password<br>• Anonymous access | • Local filesystem<br>• S3-compatible buckets | • MD5 checksum verification<br>• Batch downloads<br>• Directory downloads (recursive) |
| **SSH/SFTP** | • SSH key authentication<br>• Username/password | • Local filesystem<br>• S3-compatible buckets | • JASMIN GWS filesystem access<br>• MD5 checksum verification<br>• Batch downloads<br>• Directory downloads (recursive) |

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-protocol support** | Download from HTTP/HTTPS, FTP, SSH/SFTP sources |
| **Flexible authentication** | CEDA tokens, username/password, SSH keys, or no-auth for public data |
| **Dual destination modes** | Save to local disk or stream directly to S3-compatible buckets |
| **Integrity verification** | Optional MD5 checksum validation for all protocols |
| **Progress tracking** | Console progress bar with automatic log-based fallback |
| **Batch operations** | Download multiple files using pipe-separated URLs |
| **Recursive downloads** | Download entire directory trees from any protocol |
| **Config file support** | JSON-based configuration to avoid repeating command-line flags |
| **DAFNI integration** | Designed for use as a model step in DAFNI workflows |
| **JASMIN GWS access** | Direct access to JASMIN Group Workspace remote filesystems via SSH |

### Supported Combinations

The tool supports **54+ feature combinations**, including:

- **18 source/auth combinations** (3 protocols × 6 auth methods)
- **×2 destination types** (local filesystem or S3)
- **×3 download modes** (single file, batch, or directory)
- Additional permutations with checksum verification, progress tracking, and config file usage

## Quick Start

Install the tool:

```bash
pip install git+https://github.com/dafnifacility/dataset-download-tool.git
```

Download a public file:

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1 --dest ./data/
```

Download with CEDA credentials:

```bash
dataset-download-tool --username $CEDA_USERNAME --password $CEDA_PASSWORD --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/
```

All commands also work with the `ddt` shorthand:

```bash
ddt --help
```

## Resources

1. [CEDA: Create Archive Access Tokens](https://help.ceda.ac.uk/article/5100-archive-access-tokens)
2. [CEDA: Accounts Login or Register](https://help.ceda.ac.uk/article/39-ceda-account)
3. [CEDA: Datasets Help](https://help.ceda.ac.uk/category/13-archiving-data-with-ceda)
4. [JASMIN: GWS Setup](https://help.jasmin.ac.uk/docs/short-term-project-storage/apply-for-access-to-a-gws/)
5. [JASMIN: Public GWS Access Data](https://gws-access.jasmin.ac.uk/)
