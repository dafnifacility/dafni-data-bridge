import argparse
import json
import logging
from pathlib import Path

from dataset_download_tool.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads configuration from a JSON file and merges with CLI arguments.
    CLI arguments always take overwrite config file values.
    """

    def __init__(self):
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Download files from CEDA archives",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
            Examples:
            # download with token
            ceda-download-tool --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/

            # generate token and download
            ceda-download-tool --username USER --password PASS --url https://dap.ceda.ac.uk/...

            # download with debug logging
            ceda-download-tool --token YOUR_TOKEN --url URL --debug

            cdtool can be used as shorthand for ceda-download-tool
            """,
        )

        # authentication options
        auth_group = parser.add_mutually_exclusive_group(required=True)
        auth_group.add_argument(
            "--config",
            "-c",
            type=Path,
            metavar="FILE",
            help="Path to JSON config file",
        )
        auth_group.add_argument("--token", "-t", help="ceda access token")
        auth_group.add_argument("--username", "-u", type=str, help="ceda username (requires --password)")
        parser.add_argument(
            "--password",
            "-p",
            type=str,
            help="ceda password (required with --username). can also be set via PASSWORD env var",
        )
        auth_group.add_argument("--no-auth", "-n", action="store_true", help="if file does not need any credentails")
        parser.add_argument("--ssh", help="connect to ssh server")

        # download options
        download_group = parser.add_mutually_exclusive_group(required=False)
        download_group.add_argument("--url", help="url to download")
        download_group.add_argument("--ssh-download-path", "-dp", help="path of file to download")
        parser.add_argument(
            "--dest", "-d", default=".", help="destination path or directory (default: current directory)"
        )
        parser.add_argument("--checksum", action="store_true", help="calculate md5 checksum of downloaded file")
        parser.add_argument("--no-progress", action="store_true", help="disable progress bar")

        # session options
        parser.add_argument("--timeout", type=int, default=30, help="request timeout in seconds (default: 30)")
        parser.add_argument("--retries", type=int, default=3, help="maximum retry attempts (default: 3)")
        parser.add_argument("--key-filename", "-kf", type=str, help="ssh private keyfile")

        # logging options
        parser.add_argument("--debug", action="store_true", help="enable debug logging")
        parser.add_argument("--log-file", help="path to log file")

        return parser

    def _load_config_file(self, path: Path) -> dict:
        try:
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise ValidationError(f"Config file not found: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"file must be in JSON format: {e}")

    def _merge(self, cli_args: argparse.Namespace, file_data: dict) -> argparse.Namespace:
        """
        For each key in file_data, only apply it when the CLI did not provide a value.
        """
        merged = vars(cli_args).copy()
        defaults = {None, "", False}

        for key, file_value in file_data.items():
            if key == "config":
                continue
            if key not in merged:
                continue
            if merged[key] in defaults:
                if isinstance(merged[key], bool):
                    merged[key] = True
                else:
                    merged[key] = file_value

        return argparse.Namespace(**merged)

    def _validate(self, config: argparse.Namespace) -> None:
        if config.username and not config.ssh and not config.password:
            self.parser.error("--username requires --password unless --ssh is used")

        if config.token and config.ssh:
            self.parser.error("--ssh cannot be used with --token")

        if config.ssh and not config.username:
            self.parser.error("--ssh can only be used with --username")

        if config.no_auth and config.ssh:
            self.parser.error("--ssh cannot be used with --no-auth")

        if config.url and config.ssh_download_path:
            self.parser.error("--url cannot be used with --ssh-download-path")

        if not config.url:
            self.parser.error("--url is required (provide it on the CLI or set 'url' in your config file).")

    def parse(self, argv=None) -> argparse.Namespace:
        """
        Parse and merge configuration
        Returns an argparse.Namespace
        """
        cli_args = self.parser.parse_args(argv)

        if cli_args.config:
            file_data = self._load_config_file(cli_args.config)
            config = self._merge(cli_args, file_data)
        else:
            config = cli_args

        self._validate(config)
        return config
