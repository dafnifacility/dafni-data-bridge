# DAFNI Data Bridge 

This tool provides a unified interface for downloading files from various sources, such as SSH, HTTP, and FTP servers, including CEDA and GWS.
It saves the downloaded files to a specified destination, such as a local disk or S3-compatible buckets.

It supports authentication via CEDA tokens, username/password, or SSH keys, and can optionally verify file integrity using MD5 checksums.

## Prerequisite

## 📦 Installation

```bash
pip install git+https://github.com/dafnifacility/dataset-download-tool.git
```

Using `uv`:

```bash
uv add git+https://github.com/dafnifacility/dataset-download-tool.git
```

```sh
source ./.venv/bin/activate
```

## ⚠️ Important: Using Quotes for URLs

**Always use quotes around URLs**, especially when:
- URLs contain special shell characters (`?`, `&`, `|`)
- Downloading multiple files (separated by `|`)

```bash
# CORRECT - with quotes
dataset-download-tool --no-auth --url "https://example.com/file.txt" --dest ./data/

# CORRECT - multiple URLs with quotes
dataset-download-tool --token TOKEN --url "url1 | url2" --dest ./data/

# WRONG - without quotes (will cause shell errors)
dataset-download-tool --no-auth --url https://example.com/file.txt --dest ./data/
```

If you see shell errors like `no matches found`, make sure you're using quotes around your URLs!

Run all examples together:

```bash
export CEDA_USERNAME=...
export CEDA_PASSWORD=...
export CEDA_TOKEN=...
export JASMIN_USERNAME=...
export ACCESS_KEY=...
export SECRET_KEY=...
export S3_MINIO_DEST=
export S3_STFC_DEST=
./scripts/run_cli_examples.sh
```

## Documentation

Open the document:

```sh
# install
uv sync --extra docs

# load server
uv run mkdocs serve --livereload # live reload during editing
uv run mkdocs serve              # without live reloading 
```

To print the entire website as a PDF document open: http://localhost:8000/print_page and print as PDF.


### Publish as page

Go to https://github.com/dafnifacility/dataset-download-tool/settings/pages

- Set Source to GitHub Actions
- The docs will then be available at 🌐 https://dafnifacility.github.io/dataset-download-tool/.
