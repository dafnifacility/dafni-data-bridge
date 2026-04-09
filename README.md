# Dataset Download Tool

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

Open the document:

```sh
uv sync --extra docs
uv run mkdocs serve
# live reload during editing
uv run mkdocs serve --livereload 
```

## Publish as page

Go to https://github.com/dafnifacility/dataset-download-tool/settings/pages

- Set Source to GitHub Actions
- The docs will then be available at https://dafnifacility.github.io/dataset-download-tool/.
