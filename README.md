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
2. 🌿 API
3. 📊 DAFNI Model

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

The following flags are mutually exclusive and **cannot** be used together: `--url` and  `--ssh-download-path` TODO:


Environment Variables

TODO: In cases like user name or password you can set them using env variables just like any shell commans.  
We can call environment variables when running in CLI.


```bash
$ export USERNAME=<username>
$ export PASSWORD=<password>
$ export YOUR_TOKEN=<token>
```

We will use use USERNAME ....

---

### 🔐 Authentication Methods

TODO: all command template should be updated followed by one or more examples.


**1. No Authentication**

For publicly accessible files that require no credentials.

```bash
dataset-download-tool --no-auth --url <url of the source file> --dest <path where to save>

# example 1:

dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/path/to/public/file --dest ./data/


```

**2. Username & Password Authentication**

Authenticate using a CEDA access token. Please see the [link]() to get CEDA token.
Authenticate using your CEDA credentials. The tool will generate a token automatically. 

```bash
dataset-download-tool --username <user name> --password <password> --url <url>

# example 1:
dataset-download-tool --username $USERNAME --password $PASSWORD --url <url>
```

**3. Token Authentication**

Authenticate using a CEDA access token. Please see the [link]() to get CEDA token.

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/path/to/file --dest ./data/

# example 1:
```

**4. SSH Authentication for Remote Filesystem Access**

Connect to an SSH server and download a file by remote path.

```bash
dataset-download-tool --ssh login.jasmin.ac.uk --ssh-download-path /gws/j07/remote/file.nc --key-filename ~/.ssh/id_rsa --dest ./data/

# example 1:

```
 


### ⬇️ Download Options

TODO: all command template should be updated followed by one or more examples.


#### HTTP Downloads

**1. Token + CEDA URL + destination:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/

# example 1:
```

**2. Token + CEDA URL + checksum verification:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/ --checksum

# example 1:
```

**3. Token + URL + no progress bar:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1  --dest ./data/ --no-progress

# example 1:
```

**4. Token + CEDA URL + custom timeout and retries:**

```bash
dataset-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --timeout 60 --retries 5

# example 1:
```

**5. Username/password + CEDA URL + destination:**

```bash
dataset-download-tool --username USER --password PASS --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 --dest ./data/

# example 1:
```

**6. Username/password + CEDA URL list + destination:**

```bash
dataset-download-tool --username USER --password PASS --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt?download=1 | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/FILES_ON_TAPE.txt?download=1" --dest ./data/

# example 1:
```

> **Note:** each file url is seperated with a `|`

**7. Username/password + CEDA URL directory + destination:**

```bash
dataset-download-tool --username USER --password PASS --url "https://data.ceda.ac.uk/badc/ar6_wg1/data/ch_07/inputdata_ch7_fig18/v20220721/" --dest ./data/

# example 1:
```

> **Note:** all files in the directory are installed

**8. No auth + CEDA URL + destination:**

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/00README.txt?download=1 --dest ./data/ --checksum

# example 1:
```

**9. No auth + GWS URL + destination:**

```bash
dataset-download-tool --no-auth --url https://gws-access.jasmin.ac.uk/public/accord/ACCORD_SEAsia/GRIDT/SEAsia_HAD_5d_19910101_19911231_gridT.nc --dest ./data/ --checksum


# example 1:
```

#### FTP downloads

**10 .Username/password + URL + destination:**

```bash
dataset-download-tool --username anonymous --password user@email.com --url ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/ --dest ./data/


# example 1:
```

#### SSH Downloads

**11. SSH + private key + destination:**

```bash
dataset-download-tool --ssh login.jasmin.ac.uk --ssh-download-path /jws/j07/path/to/file --key-filename ~/.ssh/id_rsa --dest ./data/ --checksum


# example 1:
```

#### Save to S3

**12. No auth + CEDA URL + S3 destination:**

> **Note:** You must have your S3 endpoint setup with ACCESS and SECRET key set as environment variables
>
> ```bash
> $ export ACCESS_KEY=[access_key]
> $ export SECRET_KEY=[secret_key]
> ```

Can be used with any download mechanism only `--dest` should point to a S3 bucket

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/00README.txt?download=1  --dest https://bucket.s3.echo..ac.uk/key --checksum


# example 1:
```

#### Save to Local Filesystem

**13. No auth + CEDA URL + dest:**

```bash
dataset-download-tool --no-auth --url https://dap.ceda.ac.uk/badc/00README.txt?download=1 --dest ./data/

# example 1:
```

 

### 📝 Config File

TODO: There should be few more examples.


Use a JSON config file to avoid repeating flags.

Use the example config `config.example.json`

```bash
dataset-download-tool --config <json file>

# example 1:
cp config.example.json config.json
dataset-download-tool --config config.json
```


Any CLI arg will overwrite config path. For example, in the example config we set `"dest": "./data/",` but you can overwrite that in the CLI using:

```bash
dataset-download-tool --config config.json --dest /different/path/
```


### Various Examples

TODO: delete this section and move the examples there. 
Example means it can be copy paste to terminal and iy should work.

**Full HTTP download with all options:**

```bash
dataset-download-tool \
  --token YOUR_TOKEN \
  --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 \
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
  --url https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK?download=1 \
  --dest ./data/ \
  --checksum \
  --timeout 60 \
  --retries 5 \
  --debug \
  --log-file ./download.log
```

Shorthand (ddt)

All commands can be run using `ddt` instead of `dataset-download-tool`:

```bash
ddt --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/
ddt -t YOUR_TOKEN -u USER -p PASS -d ./data/
```


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
