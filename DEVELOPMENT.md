# Development Document

## ✅ Prerequisites
 
Before you begin, ensure you have the following installed:
 
- **Python** `>= 3.10`
- **uv** — Python package and project manager. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it.
- **s3cmd** (optional) — To setup S3 bucket connection


## 🚀 Getting Started

### Clone the repository:
```bash
$ git clone https://github.com/dafnifacility/dataset-download-tool.git
Cloning into 'dataset-download-tool'...
remote: Enumerating objects: 288, done.
remote: Counting objects: 100% (288/288), done.
remote: Compressing objects: 100% (180/180), done.
Receiving objects: 100% (288/288), 1.23 MiB | 4.56 MiB/s, done.

$ cd dataset-download-tool
```
### s3cmd setup 

You do not need to install s3cmd to upload to a S3 bucket but you can use it for testing purposes.
```bash
$ uv pip install s3cmd
```

All you need to set are the access and secret key for upload:

```bash
$ export ACCESS_KEY=[access_key]
$ export SECRET_KEY=[secret_key]
```

To access the bucket and view data you can configure s3cmd
```bash
$ s3cmd --configure
  Access Key: [access_key]
  Secret Key: [secret_key]
  Default Region: US
  S3 Endpoint: s3.echo.stfc.ac.uk
  DNS-style bucket+hostname:port template for accessing a bucket: s3.echo.stfc.ac.uk
  Encryption password: 
  Path to GPG program: /usr/bin/gpg
  Use HTTPS protocol: True
  HTTP Proxy server name: 
  HTTP Proxy server port: 0
```
Then use s3cmd to list the buckets

```bash
$ s3cmd ls
```


## 📦 Environment Setup

Sync all dependencies (including optional extras) into a virtual environment:
```bash
$ uv sync --all-extras
```
To install a specific extra group (e.g. `dev` | `testing`):
 
```bash
$ uv sync --extra dev
```

## 💻 Running the CLI
 
Run the tool directly using `uv run`, which ensures the correct environment is always used:
 
```bash
$ uv run dataset-download-tool --help
```

### 📥 Example Usage
 
Download a specific dataset with debug logs:
 
```bash
$ uv run dataset-download-tool -no-auth --url https://dap.ceda.ac.uk/badc/file.txt --dest ./data/ --debug
```

### 🪝 Pre-commit Hooks (Recommended)
 
Install pre-commit hooks to automatically run checks before each commit:
 
```bash
$ uv run pre-commit install
```

## 🧪 Testing
 
Run the full test suite:
 
```bash
$ uv run pytest
```
Run with coverage report:
 
```bash
$ uv run pytest --cov=dataset_download_tool --cov-report=term-missing
```