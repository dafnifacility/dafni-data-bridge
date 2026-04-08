# Installation

## Prerequisites

- **Python** >= 3.12
- Access to one or more of the following (depending on your use case):
  - [CEDA Account](https://help.ceda.ac.uk/article/39-ceda-account) and [access token](https://help.ceda.ac.uk/article/5100-archive-access-tokens)
  - [JASMIN Account](https://help.jasmin.ac.uk/docs/short-term-project-storage/apply-for-access-to-a-gws/) with GWS access
  - SSH key configured for JASMIN login nodes

## Install

```bash
# via pip
pip install git+https://github.com/dafnifacility/dataset-download-tool.git

# via uv
uv add git+https://github.com/dafnifacility/dataset-download-tool.git
```

## Verify Installation

```bash
dataset-download-tool --help
```

### Shorthand

All commands can use `ddt` instead of `dataset-download-tool`:

```bash
ddt --help
```
