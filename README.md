# Dataset Download Tool

This tool provides a unified interface for downloading files from various sources, such as SSH, HTTP, and FTP servers, including CEDA and GWS.
It saves the downloaded files to a specified destination, such as a local disk or S3-compatible buckets.

It supports authentication via CEDA tokens, username/password, or SSH keys, and can optionally verify file integrity using MD5 checksums.

## Installation

```bash
pip install git+https://github.com/dafnifacility/dataset-download-tool.git
```


The tool can be used TODO

1. CLI
2. DAFNI Model
3. API -- 


## CLI

```
dataset-download-tool -h
```

The tool supports the following parameters:

| Flag                       | Shorthand     | Description                                                |
| -------------------------- | ------------- | ---------------------------------------------------------- |
| `--config FILE`            | `-c FILE`     | Path to JSON config containing download options            |
| `--token TOKEN`            | `-t TOKEN`    | CEDA access token                                          |
| `--username USERNAME`      | `-u USERNAME` | CEDA username (requires `--password`)                      |
| `--password PASSWORD`      | `-p PASSWORD` | CEDA password (or set via `PASSWORD` env var)              |
| `--no-auth`                | `-n`          | Use when file requires no credentials                      |
| `--ssh SSH`                |               | Connect to SSH server                                      |
| `--url URL`                |               | URL to download                                            |
| `--ssh-download-path PATH` | `-dp PATH`    | Path of file to download over SSH                          |
| `--dest DEST`              | `-d DEST`     | Destination path or directory (default: current directory) |
| `--checksum`               |               | Calculate MD5 checksum of downloaded file                  |
| `--no-progress`            |               | Disable progress bar                                       |
| `--timeout TIMEOUT`        |               | Request timeout in seconds (default: 30)                   |
| `--retries RETRIES`        |               | Maximum retry attempts (default: 3)                        |
| `--key-filename FILE`      | `-kf FILE`    | SSH private key file                                       |
| `--debug`                  |               | Enable debug logging                                       |
| `--log-file FILE`          |               | Path to log file                                           |

The following flags are mutually exclusive and **cannot** be used together:

|         |                       |
| ------- | --------------------- |
| `--url` | `--ssh-download-path` |


---

### 🔐 Authentication Methods

**1. No Authentication**

For publicly accessible files that require no credentials.

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/path/to/public/file --dest ./data/
```

**2. Token Authentication**

Authenticate using a CEDA access token.

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/path/to/file --dest ./data/
```

**3. Username & Password Authentication**

Authenticate using your CEDA credentials. The tool will generate a token automatically.

```bash
dataset-download-tool --username USER --password PASS --url https://dap.ceda.ac.uk/path/to/file
```

**4. SSH Authentication for Remote Filesystem Access**

Connect to an SSH server and download a file by remote path.

```bash
dataset-download-tool --ssh ssh.ceda.ac.uk --ssh-download-path /path/to/remote/file --key-filename ~/.ssh/id_rsa --dest ./data/
```

---

### ⬇️ Download Options

#### HTTP Downloads

**1. Token + CEDA URL + destination:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/
```

**2. Token + CEDA URL + checksum verification:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/ --checksum
```

**3. Token + URL + no progress bar:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/...  --dest ./data/ --no-progress
```

**4. Token + CEDA URL + custom timeout and retries:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --timeout 60 --retries 5
```

**5. Username/password + CEDA URL + destination:**

```bash
dataset-download-tool --username USER --password PASS --url https://dap.ceda.ac.uk/... --dest ./data/
```

**6. Username/password + CEDA URL list + destination:**

```bash
dataset-download-tool --username USER --password PASS --url "https://dap.ceda.ac.uk/file1.nc... | https://dap.ceda.ac.uk/file2.nc..." --dest ./data/
```

> **Note:** each file url is seperated with a `|`

**7. Username/password + CEDA URL directory + destination:**

```bash
dataset-download-tool --username USER --password PASS --url "https://dap.ceda.ac.uk/directory..." --dest ./data/
```

> **Note:** all files in the directory are installed

**8. No auth + CEDA URL + destination:**

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/... --dest ./data/ --checksum
```

**9. No auth + GWS URL + destination:**

```bash
dataset-download-tool --no-auth --url https://gws-access.jasmin.ac.uk/path/to/file... --dest ./data/ --checksum
```

#### FTP downloads

**10 .Username/password + URL + destination:**

```bash
dataset-download-tool --username anonymous --password user@email.com --url ftp://anon-ftp.ceda.ac.uk/ --dest ./data/
```


#### SSH Downloads

**11. SSH + private key + destination:**

```bash
dataset-download-tool --ssh ssh.ceda.ac.uk --ssh-download-path /remote/path/to/file --key-filename ~/.ssh/id_rsa --dest ./data/ --checksum
```

#### Save to S3

**12. No auth + CEDA URL + S3 destination:**

Can be used with any download mechanism only `--dest` points to an S3 bucket

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/... --dest https://bucket.s3.echo..ac.uk/path --checksum
```

> **Note:** You must have your S3 endpoint setup with ACCESS and SECRET key set as environment variables

#### Save to Local Filesystem

**13. TODO:**


```bash
TODO
```

---

### Config File

TODO: 

Use a JSON config file to avoid repeating flags.


Use the example config `config.example.json`

```bash
cp config.example.json config.json
``` 

```bash
dataset-download-tool --config config.json
```

⚠️ TODO: Expand it config file + override a single flag:

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


### Various Examples

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

Shorthand (ddtool)

All commands can be run using `ddtool` instead of `dataset-download-tool`:

```bash
ddtool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/
ddtool -t YOUR_TOKEN -u USER -p PASS -d ./data/
```

---

### Environment Variables

TODO: does this tool take PASSWORD as env or other as well? Write a sentence.


| Variable   | Equivalent Flag | Description           |
| ---------- | --------------- | --------------------- |
| `PASSWORD` | `--password`    | CEDA account password |

---

## DAFNI Model

TODO: Link it

---

## API

TODO:

---

## Resources

TODO: CEDA data, token, login 

1. [CEDA: Using Archive Access Tokens](https://cds.climate.copernicus.eu/how-to-api)
