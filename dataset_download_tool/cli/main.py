import logging
import sys

from dataset_download_tool.cli.config_parser import ConfigLoader
from dataset_download_tool.exceptions import (
    AuthenticationRequiredError,
    AuthError,
    BucketNotFoundError,
    DownloadError,
    HTTPError,
    TokenValidationError,
    ValidationError,
)
from dataset_download_tool.logger import setup_logging
from dataset_download_tool.transport.client import Client


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
            url=url, 
            destination=args.dest, 
            show_progress=not args.no_progress, 
            calculate_checksum=args.checksum, 
            storage=args.storage,
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

    except AuthenticationRequiredError as e:
        logger.error(f"authentication required: {e}")
        if args.no_auth:
            logger.info("Tip: The file may require authentication. Remove --no-auth and use --token or --username/--password")
        sys.exit(1)

    except HTTPError as e:
        if e.url:
            logger.error(f"HTTP error for {e.url}: {e}")
        else:
            logger.error(f"HTTP error: {e}")
        if e.status_code:
            logger.info(f"HTTP status code: {e.status_code}")
        sys.exit(1)

    except DownloadError as e:
        if args.url:
            logger.error(f"download failed for {args.url}: {e}")
        elif args.ssh_download_path:
            logger.error(f"download failed for {args.ssh_download_path}: {e}")
        else:
            logger.error(f"download failed: {e}")
        logger.info("Tip: For multiple files, use quotes: --url \"url1 | url2\"")
        sys.exit(1)

    except BucketNotFoundError as e:
        logger.error(f"upload failed | {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("download cancelled by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
