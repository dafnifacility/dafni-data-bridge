# Ceda Dafni Data Federation

## Getting started

## Installation

```bash
pip install git+https://github.com/dafnifacility/dataset-download-tool.git
```
>**TEMPORARY DEVELOPMENT NOTE** ` pip install git+https://${GITHUB_TOKEN}@github.com/dafnifacility/dataset-download-tool.git` a token can be generated in [github developer settings ](https://github.com/settings/tokens) using classic token

## Usage

```
dataset-download-tool -h
```
## Options Reference

| Flag | Shorthand | Description |
|------|-----------|-------------|
| `--config FILE` | `-c FILE` | Path to JSON config file |
| `--token TOKEN` | `-t TOKEN` | CEDA access token |
| `--username USERNAME` | `-u USERNAME` | CEDA username (requires `--password`) |
| `--password PASSWORD` | `-p PASSWORD` | CEDA password (or set via `PASSWORD` env var) |
| `--no-auth` | `-n` | Use when file requires no credentials |
| `--ssh SSH` | | Connect to SSH server |
| `--url URL` | | URL to download |
| `--ssh-download-path PATH` | `-dp PATH` | Path of file to download over SSH |
| `--dest DEST` | `-d DEST` | Destination path or directory (default: current directory) |
| `--checksum` | | Calculate MD5 checksum of downloaded file |
| `--no-progress` | | Disable progress bar |
| `--timeout TIMEOUT` | | Request timeout in seconds (default: 30) |
| `--retries RETRIES` | | Maximum retry attempts (default: 3) |
| `--key-filename FILE` | `-kf FILE` | SSH private key file |
| `--debug` | | Enable debug logging |
| `--log-file FILE` | | Path to log file |

> **Note:** `--url` and `--ssh-download-path` are mutually exclusive.

## Authentication Methods

### 1. Token Authentication
Authenticate using a CEDA access token.

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/path/to/file --dest ./data/
```

### 2. Username & Password Authentication
Authenticate using your CEDA credentials. The tool will generate a token automatically.

```bash
dataset-download-tool --username USER --password PASS --url https://dap.ceda.ac.uk/path/to/file
```

### 3. No Authentication
For publicly accessible files that require no credentials.

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/path/to/public/file --dest ./data/
```

### 4. SSH Authentication
Connect to an SSH server and download a file by remote path.

```bash
dataset-download-tool --ssh ssh.ceda.ac.uk --ssh-download-path /path/to/remote/file --key-filename ~/.ssh/id_rsa --dest ./data/
```

## All Flag Combinations

### HTTP Downloads

**Token + CEDA URL + destination:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/
```

**Token + CEDA URL + checksum verification:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/ --checksum
```

**Token + URL + no progress bar:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/...  --dest ./data/ --no-progress
```

**Token + CEDA URL + custom timeout and retries:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --timeout 60 --retries 5
```

**Username/password + CEDA URL + destination:**
```bash
dataset-download-tool --username USER --password PASS --url https://dap.ceda.ac.uk/... --dest ./data/
```

**Username/password + CEDA URL list + destination:** 
```bash
dataset-download-tool --username USER --password PASS --url "https://dap.ceda.ac.uk/file1.nc... | https://dap.ceda.ac.uk/file2.nc..." --dest ./data/
```
> **Note:**  each file url is seperated with a `|`

**Username/password + CEDA URL directory + destination:** 
```bash
dataset-download-tool --username USER --password PASS --url "https://dap.ceda.ac.uk/directory..." --dest ./data/
```
> **Note:**  all files in the directory are installed

**No auth + CEDA URL + destination:**
```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/... --dest ./data/ --checksum
```

**No auth + GWS URL + destination:**
```bash
dataset-download-tool --no-auth --url https://gws-access.jasmin.ac.uk/path/to/file... --dest ./data/ --checksum
```
---
### FTP downlaods

**Username/password + URL + destination:**
```bash
dataset-download-tool --username anonymous --password user@email.com --url ftp://anon-ftp.ceda.ac.uk/ --dest ./data/
```
---
### SSH Downloads
**SSH + private key + destination:**
```bash
dataset-download-tool --ssh ssh.ceda.ac.uk --ssh-download-path /remote/path/to/file --key-filename ~/.ssh/id_rsa --dest ./data/ --checksum
```
---
### Upload to S3
**No auth + CEDA URL + S3 destination:**

Can be used with any download mechanism only `--dest` points to an S3 bucket 
```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/... --dest https://bucket.s3.echo..ac.uk/path --checksum
```
> **Note:** You must have your S3 endpoint setup with ACCESS and SECRET key set as environment variables
---

### Config File

Use a JSON config file to avoid repeating flags.

```bash
dataset-download-tool --config config.json
```

Example `config.json`:
```json
{
  "token": "YOUR_TOKEN",
  "url": "https://dap.ceda.ac.uk/path/to/file",
  "dest": "./data/",
  "checksum": true,
  "retries": 5,
  "timeout": 60
}
```

Config file + override a single flag:
```bash
dataset-download-tool --config config.json --dest /different/path/
```

---

### Logging & Debugging

**Enable debug logging:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --debug
```

**Write logs to a file:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --log-file ./download.log
```

**Debug logging to file:**
```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --debug --log-file ./download.log
```

---

### Combined Examples

**Full HTTP download with all options:**
```bash
dataset-download-tool \
  --token YOUR_TOKEN \
  --url https://dap.ceda.ac.uk/path/to/file \
  --dest ./data/ \
  --checksum \
  --timeout 60 \
  --retries 5 \
  --no-progress \
  --debug \
  --log-file ./download.log
```

**Full SSH download with all options:**
```bash
dataset-download-tool \
  --ssh ssh.ceda.ac.uk \
  --ssh-download-path /remote/path/to/file \
  --key-filename ~/.ssh/id_rsa \
  --dest ./data/ \
  --checksum \
  --timeout 60 \
  --retries 5 \
  --debug \
  --log-file ./download.log
```

**Username/password with all options:**
```bash
dataset-download-tool \
  --username USER \
  --password PASS \
  --url https://dap.ceda.ac.uk/path/to/file \
  --dest ./data/ \
  --checksum \
  --timeout 60 \
  --retries 5 \
  --debug \
  --log-file ./download.log
```

---

## Shorthand (ddtool)

All commands can be run using `ddtool` instead of `dataset-download-tool`:

```bash
ddtool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/
ddtool -t YOUR_TOKEN -u USER -p PASS -d ./data/
```

---

## Mutually Exclusive Flags

The following flags **cannot** be used together:

| Flag A | Flag B |
|--------|--------|
| `--url` | `--ssh-download-path` |

---

## Environment Variables

| Variable | Equivalent Flag | Description |
|----------|----------------|-------------|
| `PASSWORD` | `--password` | CEDA account password |

## Documentation

### Features

To be added, see internal document.
 

## Resources

1. [CEDA: Using Archive Access Tokens](https://cds.climate.copernicus.eu/how-to-api)

## Authors and acknowledgment

xx

## License

xx
