import logging
import sys

from ceda_download_tool.cli.config_parser import ConfigLoader
from ceda_download_tool.exceptions import (
    AuthError,
    BucketNotFoundError,
    DownloadError,
    TokenValidationError,
    ValidationError,
)
from ceda_download_tool.logger import setup_logging
from ceda_download_tool.transport.client import Client


def main():
    logger = logging.getLogger(__name__)

    try:
        args = ConfigLoader().parse()
        # setup logging
        log_level = logging.DEBUG if args.debug else logging.INFO
        setup_logging(level=log_level, log_file=args.log_file)
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
        logger.error(f"invalid input: {e}")
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
