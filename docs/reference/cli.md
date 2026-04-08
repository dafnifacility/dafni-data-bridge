# CLI Module

## `main()`

::: dataset_download_tool.cli.main.main

Entry point for the `dataset-download-tool` / `ddt` command. Orchestrates:

1. Parsing configuration via `ConfigLoader`
2. Setting up logging (debug level if `--debug`)
3. Creating the appropriate `Client` based on auth method
4. Calling `client.download()`
5. Printing results (destination, size, checksum)

**Exit codes:**

| Exception              | Code | Message                 |
| ---------------------- | ---- | ----------------------- |
| `ValidationError`      | 1    | Invalid input           |
| `TokenValidationError` | 1    | Token validation failed |
| `AuthError`            | 1    | Authentication failed   |
| `DownloadError`        | 1    | Download failed         |
| `BucketNotFoundError`  | 1    | S3 upload failed        |
| `KeyboardInterrupt`    | 130  | Cancelled by user       |

---

## `ConfigLoader`

::: dataset_download_tool.cli.config_parser.ConfigLoader

Loads and merges JSON config files with CLI arguments. CLI arguments take precedence over config file values.

### Methods

#### `parse(argv=None) -> argparse.Namespace`

Main entry point. Parses CLI args, optionally loads a config file, merges them, and validates the result.

**Parameters:**

- `argv` — Optional list of CLI arguments. Defaults to `sys.argv`.

**Returns:** `argparse.Namespace` with all resolved configuration values.

#### `_build_parser() -> argparse.ArgumentParser`

Constructs the argument parser with these groups:

- **Authentication** (mutually exclusive, required): `--config`, `--token`, `--username`, `--no-auth`, `--ssh`
- **Download**: `--url`, `--ssh-download-path`
- **Session options**: `--timeout`, `--retries`, `--key-filename`
- **Download options**: `--dest`, `--checksum`, `--no-progress`
- **Logging**: `--debug`, `--log-file`

#### `_load_config_file(path) -> dict`

Reads and parses a JSON config file.

#### `_merge(cli_args, file_data) -> argparse.Namespace`

Merges CLI arguments with config file data. CLI values take priority — config file values are only used for arguments not explicitly provided on the command line.

#### `_validate(config) -> None`

Validates argument combinations:

- `--username` requires `--password` (unless SSH mode)
- `--ssh` cannot be used with `--token` or `--no-auth`
- `--ssh` requires `--username`
- `--ssh` uses `--ssh-download-path`, not `--url`
- Must provide either `--url` or `--ssh-download-path`
