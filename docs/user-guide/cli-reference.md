# CLI Reference

```
dataset-download-tool [OPTIONS]
```

## Flags

| Flag                       | Shorthand          | Description                                                |
| -------------------------- | ------------------ | ---------------------------------------------------------- |
| `--config FILE`            | `-c FILE`          | Path to JSON config containing download options            |
| `--token CEDA_TOKEN`       | `-t CEDA_TOKEN`    | CEDA access token                                          |
| `--username CEDA_USERNAME` | `-u CEDA_USERNAME` | CEDA username (requires `--password`)                      |
| `--password CEDA_PASSWORD` | `-p CEDA_PASSWORD` | CEDA password (or set via `CEDA_PASSWORD` env var)         |
| `--no-auth`                | `-n`               | Use when file requires no credentials                      |
| `--ssh SSH`                |                    | Connect to SSH server                                      |
| `--url URL`                |                    | URL to download                                            |
| `--ssh-download-path PATH` | `-dp PATH`         | Path of file to download over SSH                          |
| `--dest DEST`              | `-d DEST`          | Destination path or directory (default: current directory) |
| `--checksum`               |                    | Calculate MD5 checksum of downloaded file                  |
| `--no-progress`            |                    | Disable progress bar                                       |
| `--timeout TIMEOUT`        |                    | Request timeout in seconds (default: 30)                   |
| `--retries RETRIES`        |                    | Maximum retry attempts (default: 3)                        |
| `--key-filename FILE`      | `-kf FILE`         | SSH private key file                                       |
| `--debug`                  |                    | Enable debug logging                                       |
| `--log-file FILE`          |                    | Path to log file                                           |

#### Mutually Exclusive Groups

The following flags **cannot** be used together:

- **`--url`** and **`--ssh-download-path`** — `--url` is for HTTP/HTTPS/FTP sources, `--ssh-download-path` is for JASMIN GWS server paths.
- **Authentication**: `--config`, `--token`, `--username`, `--no-auth`, and `--ssh` are mutually exclusive.

#### Environment Variables

Set sensitive information as environment variables:

```bash
export CEDA_USERNAME=<username>
export CEDA_PASSWORD=<password>
export CEDA_TOKEN=<token>
export JASMIN_USERNAME=<jasmin gws username>
```

Reference them in commands with `$VARIABLE`:

```bash
dataset-download-tool --username $CEDA_USERNAME --password $CEDA_PASSWORD --url "<url>" --dest ./data/
```

For S3 uploads, set the following:

```bash
export ACCESS_KEY=<access_key>
export SECRET_KEY=<secret_key>
```

#### Exit Codes

| Code  | Meaning                                                     |
| ----- | ----------------------------------------------------------- |
| `0`   | Success                                                     |
| `1`   | Error (validation, authentication, download, or S3 failure) |
| `130` | Cancelled by user (Ctrl+C)                                  |

#### Logging and Debugging

Enable debug logging:

```bash
dataset-download-tool --username $CEDA_USERNAME --password $CEDA_PASSWORD --url "<url>" --debug
```

Write logs to a file:

```bash
dataset-download-tool --username $CEDA_USERNAME --password $CEDA_PASSWORD --url "<url>" --log-file ./download.log
```

Both:

```bash
dataset-download-tool --username $CEDA_USERNAME --password $CEDA_PASSWORD --url "<url>" --debug --log-file ./download.log
```

---

## Download Commands

### No Authentication

For publicly accessible files that require no credentials.

```bash
dataset-download-tool --no-auth --url "<url>" --dest <path>
```

**Example:**

```bash
dataset-download-tool --no-auth \
  --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1" \
  --dest ./data/
```

### Authentication

The tool supports four authentication methods depending on the data source and access requirements.

#### Username and Password

Authenticate using CEDA credentials. Register for a [CEDA Archive account](https://accounts.ceda.ac.uk/realms/ceda/login-actions/registration?client_id=account-console&tab_id=H-sQE2Qp8_I) if you don't have one. A token is generated automatically from your credentials.

```bash
dataset-download-tool --username <user> --password <pass> --url "<url>" --dest <path>
```

**Examples:**

```bash
# Using environment variables (recommended)
dataset-download-tool --username $CEDA_USERNAME --password $CEDA_PASSWORD \
  --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1" \
  --dest ./data/

# Inline credentials
dataset-download-tool --username johndoe --password P4ssW0rd \
  --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1" \
  --dest ./data/
```

!!! tip "Verify authentication"

    If the downloaded `TOKEN_CHECK` file contains "Congratulations, you have successfully authenticated with CEDA using a token." then credentials are working correctly.

#### Token Authentication

Authenticate using a CEDA access token. Get your token from the [CEDA token page](https://services-beta.ceda.ac.uk/account/token/).

```bash
dataset-download-tool --token <token> --url "<url>" --dest <path>
```

**Example:**

```bash
dataset-download-tool --token $CEDA_TOKEN \
  --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1" \
  --dest ./data/
```

#### SSH Key Authentication

Connect to an SSH server (e.g., JASMIN) and download files by remote path.

```bash
dataset-download-tool --username <user> --ssh <host> \
  --ssh-download-path <remote-path> --key-filename <key> --dest <path>
```

**Examples:**

```bash
# Single file from JASMIN GWS
dataset-download-tool --username $JASMIN_USERNAME \
  --ssh xfer-vm-01.jasmin.ac.uk \
  --ssh-download-path /gws/pw/j07/perf_testing/1GB.zip \
  --key-filename ~/.ssh/id_rsa \
  --dest ./data/ --checksum

# Entire directory from JASMIN GWS
dataset-download-tool --username $JASMIN_USERNAME \
  --ssh xfer-vm-01.jasmin.ac.uk \
  --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
  --key-filename ~/.ssh/id_rsa \
  --dest ./data/
```

!!! warning "Security"

    Never hardcode credentials in scripts or config files that are shared. Use environment variables or secure credential stores.

### Using Configuration File

Use a JSON config file to avoid repeating CLI arguments. Start from the provided example:

```bash
cp config.example.json config.json
```

Run with:

```bash
dataset-download-tool --config config.json
```

**Examples**

**No auth + checksum:**

```json
{
  "no_auth": "",
  "url": "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1",
  "dest": "./data/",
  "checksum": ""
}
```

**Token + destination:**

```json
{
  "token": "<ceda token>",
  "url": "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1",
  "dest": "./data/",
  "checksum": ""
}
```

**Username/password:**

```json
{
  "username": "USERNAME",
  "password": "PASSWORD",
  "url": "https://dap.ceda.ac.uk/path/to/file.nc",
  "checksum": ""
}
```

**Boolean Flags**

Boolean flags default to `false`. To enable them in a config file, set the value to an empty string:

```json
{
  "checksum": "",
  "no_auth": "",
  "no_progress": ""
}
```

**CLI Precedence**

CLI arguments override config file values. For example, the following overrides the `dest` from the config file:

```bash
dataset-download-tool --config config.json --dest /different/path/
```

### Download Options

#### Multiple URLs

Separate URLs with `|`:

```bash
dataset-download-tool --no-auth \
  --url "https://dap.ceda.ac.uk/badc/file1.txt?download=1 | https://dap.ceda.ac.uk/badc/file2.txt?download=1"
```

#### Directory Downloads

Pass a directory URL to download all files within it:

```bash
dataset-download-tool --no-auth \
  --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
  --dest ./data/
```

#### GWS HTTP Downloads

Download files from JASMIN Group Workspace (GWS) public HTTP endpoints:

```bash
# Single file
dataset-download-tool --no-auth \
  --url "https://gws-access.jasmin.ac.uk/public/perf-testing/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc" \
  --dest ./data/ --checksum

# Multiple files (pipe-separated)
dataset-download-tool --no-auth \
  --url "https://gws-access.jasmin.ac.uk/public/perf-testing/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | https://gws-access.jasmin.ac.uk/public/perf-testing/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
  --dest ./data/ --checksum

# Entire directory
dataset-download-tool --no-auth \
  --url "https://gws-access.jasmin.ac.uk/public/perf-testing/testdir/" \
  --dest ./data/ --checksum
```

#### FTP Downloads

CEDA FTP server is public — use `anonymous` as username and your email as password.

!!! info

    See the [CEDA FTP help page](https://help.ceda.ac.uk/article/280-ftp) for more information.

```bash
# Single file
dataset-download-tool --username anonymous --password johndoe@email.com \
  --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
  --dest ./data/

# Multiple files (pipe-separated)
dataset-download-tool --username anonymous --password johndoe@email.com \
  --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
  --dest ./data/

# Entire directory
dataset-download-tool --username anonymous --password johndoe@email.com \
  --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
  --dest ./data/
```

#### SSH Downloads

Download files directly from JASMIN GWS via SSH:

```bash
# Single file
dataset-download-tool --username $JASMIN_USERNAME \
  --ssh xfer-vm-01.jasmin.ac.uk \
  --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
  --key-filename ~/.ssh/id_rsa \
  --dest ./data/ --checksum

# Multiple files (pipe-separated)
dataset-download-tool --username $JASMIN_USERNAME \
  --ssh xfer-vm-01.jasmin.ac.uk \
  --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
  --key-filename ~/.ssh/id_rsa \
  --dest ./data/ --checksum

# Entire directory
dataset-download-tool --username $JASMIN_USERNAME \
  --ssh xfer-vm-01.jasmin.ac.uk \
  --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
  --key-filename ~/.ssh/id_rsa \
  --dest ./data/ --checksum
```

#### S3 Destination

Stream downloads directly to an S3-compatible bucket. Set your credentials first:

```bash
export ACCESS_KEY=<access_key>
export SECRET_KEY=<secret_key>
```

Can be used with any download method — just point `--dest` at an S3 bucket:

```bash
# MinIO (local)
dataset-download-tool --no-auth \
  --url "https://dap.ceda.ac.uk/badc/00README.txt?download=1" \
  --dest "http://test.localhost:9000/data/" --checksum

# STFC Echo S3
dataset-download-tool --no-auth \
  --url "https://dap.ceda.ac.uk/badc/00README.txt?download=1" \
  --dest "https://ddttest.s3.echo.stfc.ac.uk/key" --checksum
```

!!! tip

    See the [Development Setup — S3 Setup](../developer-guide/setup.md#s3-setup-optional) section for configuring S3 endpoints.

### Timeout and Retries

```bash
dataset-download-tool --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \ --url "<url>" --dest ./data/ --timeout 60 --retries 5
```
