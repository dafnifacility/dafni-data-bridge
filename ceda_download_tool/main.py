import argparse
import logging
import sys

from ceda_download_tool.client import Client
from ceda_download_tool.exceptions import (
    AuthError,
    BucketNotFoundError,
    DownloadError,
    TokenValidationError,
    ValidationError,
)
from ceda_download_tool.logger import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="Download files from CEDA archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""

    Examples:
    # download with token
    python main.py --token YOUR_TOKEN --url https://dap.ceda.ac.uk/... --dest ./data/

    # generate token and download
    python main.py --username USER --password PASS --url https://dap.ceda.ac.uk/...

    # download with debug logging
    python main.py --token YOUR_TOKEN --url URL --debug
            """,
    )

    # authentication options
    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument("--token", "-t", help="ceda access token")
    auth_group.add_argument("--username", "-u", help="ceda username (requires --password)")
    parser.add_argument(
        "--password", "-p", help="ceda password (required with --username). can also be set via PASSWORD env var"
    )
    auth_group.add_argument("--no-auth", "-n", action="store_true", help="if file does not need any credentails")
    parser.add_argument("--ssh", help="connect to ssh server")

    # download options
    download_group = parser.add_mutually_exclusive_group(required=True)
    download_group.add_argument("--url", help="url to download")
    download_group.add_argument("--ssh-download-path", "-dp", help="path of file to download")
    parser.add_argument("--dest", "-d", default=".", help="destination path or directory (default: current directory)")
    parser.add_argument("--checksum", action="store_true", help="calculate md5 checksum of downloaded file")
    parser.add_argument("--no-progress", action="store_true", help="disable progress bar")

    # session options
    parser.add_argument("--timeout", type=int, default=30, help="request timeout in seconds (default: 30)")
    parser.add_argument("--retries", type=int, default=3, help="maximum retry attempts (default: 3)")
    parser.add_argument("--key-filename", "-kf", type=str, help="ssh private keyfile")

    # logging options
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--log-file", help="path to log file")

    args = parser.parse_args()
    if args.username and not args.ssh and not args.password:
        parser.error("--username requires --password unless --ssh is used")

    if args.token and args.ssh:
        parser.error("--ssh cannot be used with --token")

    if args.ssh and not args.username:
        parser.error("--ssh can only be used with --username")

    if args.no_auth and args.ssh:
        parser.error("--ssh cannot be used with --no-auth")

    if args.url and args.ssh_download_path:
        parser.error("--url cannot be used with --ssh-download-path")

    # setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level, log_file=args.log_file)

    logger = logging.getLogger(__name__)

    try:
        if args.ssh:
            client = Client.ssh_client(
                url=args.ssh_download_path, hostname=args.ssh, username=args.username, key_filename=args.key_filename
            )
        if args.url:
            client = Client.validate_url(url=args.url)
            if args.token:
                client = Client(url=args.url, token=args.token)
            if args.url.startswith(("ftp://")):
                client = Client.ftp_login(url=args.url, username=args.username, password=args.password)
            if args.no_auth:
                client = Client(url=args.url, token="no_auth")
            if args.username and not args.url.startswith(("ftp://")):
                client = Client.from_credentials(
                    url=args.url,
                    username=args.username,
                    password=args.password,
                    timeout=args.timeout,
                    max_retries=args.retries,
                )

        # download file
        url = args.ssh_download_path if args.ssh else args.url
        result = client.download(
            url=url, destination=args.dest, show_progress=not args.no_progress, calculate_checksum=args.checksum
        )

        # print result
        logger.info(f"downloaded: {result.destination}")
        logger.info(f"size: {result.size_mb:.2f} MB")

        if result.checksum:
            logger.info(f"md5: {result.checksum}")

        print(f"\nsuccess: {result.destination}")

    except ValidationError as e:
        logger.error(f"url validation failed: {e}")
        sys.exit(1)

    except TokenValidationError as e:
        logger.error(f"token validation failed: {e}")
        sys.exit(1)

    except AuthError as e:
        logger.error(f"authentication failed: {e}")
        sys.exit(1)

    except DownloadError as e:
        logger.error(f"download failed: {e}")
        sys.exit(1)

    except BucketNotFoundError as e:
        logger.error(f"upload failed | {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("download cancelled by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
