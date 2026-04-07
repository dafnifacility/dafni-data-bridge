# Dataset Download Tool

This tool provides a unified interface for downloading files from various sources, such as SSH, HTTP, and FTP servers, including CEDA and GWS.
It saves the downloaded files to a specified destination, such as a local disk or S3-compatible buckets.

It supports authentication via CEDA tokens, username/password, or SSH keys, and can optionally verify file integrity using MD5 checksums.

## 📦 Installation

```bash
pip install git+https://github.com/dafnifacility/dataset-download-tool.git
```

Using `uv`:

```bash
uv add git+https://github.com/dafnifacility/dataset-download-tool.git
```

The tool can be used in

1. [🖥️ CLI](#1-️-cli)
2. [🌿 API](#-api)
3. [📊 DAFNI Model](#-dafni-model)

## 1. 🖥️ CLI 

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

The following flags are mutually exclusive and **cannot** be used together: `--url` and  `--ssh-download-path` do to conflicts, `url` is specifically used to download from `http/s` or `ftp` sources, and `--ssh-download-path` for JASMiN GWS server.


#### Environment Variables

In the case of sensative information we can use env variables. These are set like any normal shell commands:

```bash
$ export USERNAME=<username>
$ export PASSWORD=<password>
$ export TOKEN=<token>
```
We can then call them when running the CLI tool with `$<VARIABLE>` E.G. `$USERNAME` (further examples in [Authentication Methods](#-authentication-methods) section).

---

### 🔐 Authentication Methods

**1. No Authentication**

For publicly accessible files that require no credentials.

```bash
dataset-download-tool --no-auth --url <url of the source file> --dest <path where to save>

# example 1:

dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1 --dest ./data/
```

**2. Username & Password Authentication**

Authenticate using a CEDA credentails. Please see the [link](https://accounts.ceda.ac.uk/realms/ceda/login-actions/registration?client_id=account-console&tab_id=H-sQE2Qp8_I) to register for CEDA Archive account. Authenticating using your CEDA credentials will generate a token automatically.

```bash
dataset-download-tool --username <user name> --password <password> --url <url of the source file> --dest <path where to save>

# example 1 with ENV variables:
dataset-download-tool --username $USERNAME --password $PASSWORD --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/

# example 2 with credentaials in CLI:
dataset-download-tool --username Username --password P4ssW0rd --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/
```
If `$(pwd)/data/TOKEN_CHECK` contains: "Congratulations, you have successfuly authenticated with CEDA using a token." this means that the credentails worked correctly and you are able to install files from CEDA Archive correctly.

**3. Token Authentication**

Authenticate using a CEDA access token. Please see the [link](https://services-beta.ceda.ac.uk/account/token/) to get CEDA token given you have already signed up for CEDA.

```bash
dataset-download-tool --token <YOUR_TOKEN> --url <url of the source file> --dest <path where to save>

# example 1 with ENV variables:
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/
```

**4. SSH Authentication for Remote Filesystem Access**

Connect to an SSH server and download a file by remote path.

```bash
dataset-download-tool --ssh <SSH server ip> --ssh-download-path <File path to download> --key-filename <SSH auth key> --dest ./data/

# example 1:
dataset-download-tool --ssh login.jasmin.ac.uk --ssh-download-path /gws/j07/remote/file.nc --key-filename ~/.ssh/id_rsa --dest ./data/
```
 
### ⬇️ Download Options

#### HTTP Downloads

**1. No auth + CEDA URL + destination:**

```bash
dataset-download-tool --no-auth --url <url of the source file> --dest <path where to save>

# example 1:

dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1 --dest ./data/
```

**2. Token + CEDA URL + destination:**

```bash
dataset-download-tool --token <YOUR_TOKEN> --url <url of the source file> --dest <path where to save>

# example 1 with ENV variables:
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/
```

**3. Token + CEDA URL + checksum verification:**

```bash
dataset-download-tool --token YOUR_TOKEN --url <url of the source file> --dest <path where to save> --checksum

# example 1:
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/ --checksum
```

**4. Token + URL + no progress bar:**

```bash
dataset-download-tool --token <YOUR_TOKEN> --url <url of the source file> --dest <path where to save> --no-progress

# example 1:
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/ --no-progress
```

**5. Token + CEDA URL + custom timeout and retries:**

```bash
dataset-download-tool --token <YOUR_TOKEN> --url <url of the source file> --dest <path where to save> --timeout 60 --retries 5

# example 1:
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/ --timeout 60 --retries 5
```

**6. Username/password + CEDA URL + destination:**

```bash
# example 1 with ENV variables:
dataset-download-tool --username $USERNAME --password $PASSWORD --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/

# example 2 with credentaials in CLI:
dataset-download-tool --username Username --password P4ssW0rd --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/
```

**7. No auth + CEDA URL list + destination:**

```bash
dataset-download-tool --no-auth --url "<url of the source file 1> | <url of the source file 2> " --dest <path where to save>

# example 1:
dataset-download-tool --username $USERNAME --password $PASSWORD --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1 | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/FILES_ON_TAPE.txt?download=1" --dest ./data/
```

> **Note:** each file url is seperated with a `|`

**8. No auth + CEDA URL directory + destination:**

```bash
dataset-download-tool --no-auth --url <Dir URL> --dest <path where to save>

# example 1:
dataset-download-tool --no-auth --url https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989 --dest ./data/
```

> **Note:** all files in the directory are installed

**9. No auth + GWS URL + destination:**

```bash
dataset-download-tool --no-auth --url <GWS URL> --dest <path where to save> --checksum

# example 1:
dataset-download-tool --no-auth --url https://gws-access.jasmin.ac.uk/public/accord/ACCORD_SEAsia/GRIDT/SEAsia_HAD_5d_19910101_19911231_gridT.nc --dest ./data/ --checksum
```

#### FTP downloads

**10. Username/password + URL + destination:**

```bash
dataset-download-tool --username anonymous --password <user email> --url <ftp file url> --dest <path where to save>

# example 1:
dataset-download-tool --username anonymous --password user@email.com --url ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/ --dest ./data/
```
> **NOTE** CEDA FTP server is public, and is accessed with `anonymous` + `email` as username and password. [More information](https://help.ceda.ac.uk/article/280-ftp) can be found on the CEDA help page

#### SSH Downloads

**11. SSH + private key + destination:**

```bash
dataset-download-tool --ssh <SSH ip> --ssh-download-path <file path to download> --key-filename <path to SSH key> --dest <path where to download> --checksum


# example 1:
dataset-download-tool --ssh login.jasmin.ac.uk --ssh-download-path /jws/j07/path/to/file --key-filename ~/.ssh/id_rsa --dest ./data/ --checksum
```

#### Save to S3

> **Note:** You must have your S3 endpoint setup with ACCESS and SECRET key set as environment variables. The tool scans for ACCESS_KEY and SECRET_KEY as ENV varibles.
>
> ```bash
> $ export ACCESS_KEY=[access_key]
> $ export SECRET_KEY=[secret_key]
> ```

Can be used with any download mechanism only `--dest` should point to a S3 bucket

**12. No auth + CEDA URL + S3 destination:**

```bash
dataset-download-tool --no-auth --url <url to download> --dest https://<bucket>.<S3 endpoint>/<key> --checksum


# example 1:
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/00README.txt?download=1 --dest https://bucket.s3.echo..ac.uk/key --checksum
```

#### Save to Local Filesystem

**13. No auth + CEDA URL + dest:**

```bash
dataset-download-tool --no-auth --url <url to download> --dest <path to save>

# example 1:
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/00README.txt?download=1 --dest ./data/
```

 
### 📝 Config File

Use a JSON config file to avoid repeating flags.

Use the example config `config.example.json`
```bash
cp config.example.json config.json
```

```bash
dataset-download-tool --config <json file path>

# example 1:
dataset-download-tool --config config.json
```


Any CLI arg will overwrite config variable. For example, in the example config we set `"dest": "./data/",` but you can overwrite that in the CLI using:

```bash
dataset-download-tool --config config.json --dest /different/path/
```

### Config Examples

> **NOTE:** All booleans variable are set to false unless invoked. To invoke them in config you can include them by setting them to `=""` e.g `"checksum": "",`

**No auth + CEDA URL + destination + checksum:**
```JSON
{
  "no_auth":"",
  "url": "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1",
  "dest": "./data/",
  "checksum": "",
}
```

**Token + CEDA URL + destination + checksum:**
```JSON
{
  "token": "<TOKEN>",
  "url": "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1",
  "dest": "./data/",
  "checksum": "",
}
```

**Token environment variable + CEDA URL + destination + checksum:**
```JSON
{
  "token": "$TOKEN",
  "url": "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1",
  "dest": "./data/",
  "checksum": "",
}
```

### Shorthand (ddt)

All commands can be run using `ddt` instead of `dataset-download-tool`:

```bash
ddt --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/
ddt -t YOUR_TOKEN -u USER -p PASS -d ./data/
```
s

### Logging & Debugging

**Enable debug logging:**

```bash
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/... --debug
```

**Write logs to a file:**

```bash
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/... --log-file ./download.log
```

**Debug logging to file:**

```bash
dataset-download-tool --token $TOKEN --url https://dap.ceda.ac.uk/... --debug --log-file ./download.log
```

---

## 🌿 API

TODO:

---


## 📊 DAFNI Model

The download tool can be used on the DAFNI Platform. Please refer to the [`MODEL_README.md`](/dafni-model/readme/MODEL_README.md). This goes over all steps on how setup the model to download the datasets on DAFNI workflows.

---

## 📋 Resources

TODO: CEDA data, token, login

1. [CEDA: Create Archive Access Tokens](https://help.ceda.ac.uk/article/5100-archive-access-tokens)
2. [CEDA: Accounts Login or Register Information](https://help.ceda.ac.uk/article/39-ceda-account)
3. [CEDA: Datasets Help](https://help.ceda.ac.uk/category/13-archiving-data-with-ceda)
4. [JASMiN: GWS Setup](https://help.jasmin.ac.uk/docs/short-term-project-storage/apply-for-access-to-a-gws/)
5. [JASMiN: Public GWS Access Data](https://gws-access.jasmin.ac.uk/)
