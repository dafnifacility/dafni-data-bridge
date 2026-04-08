# Dataset Download Tool

A unified interface for downloading files from SSH, HTTP, and FTP servers — including CEDA and JASMIN GWS — with support for saving to local disk or S3-compatible buckets.

## Features

- **Multi-protocol support** — HTTP/HTTPS, FTP, SSH/SFTP
- **CEDA authentication** — token, username/password, or no-auth for public files
- **SSH key authentication** — for JASMIN GWS remote filesystem access
- **MD5 checksum verification** — optional integrity checking
- **Progress tracking** — console progress bar with log-based fallback
- **S3 upload** — stream downloads directly to S3-compatible buckets
- **Config file support** — JSON-based configuration to avoid repeating flags
- **DAFNI platform integration** — use as a model step in DAFNI workflows
- **Batch downloads** — pipe-separated URLs for multiple file downloads
- **Directory downloads** — recursive download of entire directories

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
