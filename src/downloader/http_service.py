import hashlib
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from exceptions import DownloadError

from downloader.base import BaseDownloader
from downloader.models import DownloadResult, ProgressCallback
from downloader.utils import (
    logger,
    multiple_download_result,
    multiple_url_download,
    multiple_urls_split,
    resolve_destination,
)


class HTTPDownloader(BaseDownloader):
    """
    HTTP/S implementation of the file downloader.

    This class uses a persistent session to handle downloads, supporting chunked transfers and progress tracking.

    Args:
        session: A requests.Sessions object

    """

    CEDA_DAP_HOST = os.getenv("CEDA_DAP_HOST", "dap.ceda.ac.uk")
    DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "8192"))

    def __init__(self, session: requests.Session, chunk_size: int | None = None):
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        if chunk_size <= 0:
            raise ValueError("chunk size must be positive")

        self._session = session
        self._chunk_size = chunk_size

    def download(
        self,
        url: str,
        destination: Optional[str | Path] = None,
        progress_callback: Optional[ProgressCallback] = None,
        calculate_checksum: bool = False,
    ) -> DownloadResult:
        """
        Args:
            url: url to download from.
            destination: destination path or directory,
            if directory, filename is extracted from url,
            if None, uses current directory.
            progress_callback: optional callback(downloaded_bytes, total_bytes).
            calculate_checksum: whether to calculate md5 checksum.

        Returns:
            DownloadResult with download details.

        Raises:
            ValidationError: if url or destination is invalid.
            DownloadError: if download fails.
        """

        url = multiple_urls_split(url)

        if isinstance(url, str):
            dest_path = resolve_destination(url, destination)

            if self._is_directory(url):
                logger.info(f"Downloading directory: {url}")
                directory_download = self._recursive_download(url, dest_path, calculate_checksum, progress_callback)

                return multiple_download_result(url, directory_download)

            else:
                logger.info(f"starting download: {url}")
                logger.info(f"destination: {dest_path}")
                try:
                    response = self._session.get(url, stream=True)
                    response.raise_for_status()
                except requests.RequestException as e:
                    logger.error(f"download request failed: {e}")
                    raise DownloadError(f"failed to download {url}: {e}") from e

                total_size = int(response.headers.get("content-length", 0))
                if total_size:
                    logger.info(f"file size: {total_size / (1024 * 1024):.2f} MB")

                # Ensure parent directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                downloaded_size = 0
                md5_hash = hashlib.md5() if calculate_checksum else None

                try:
                    with open(dest_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=self._chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)

                                if md5_hash:
                                    md5_hash.update(chunk)

                                if progress_callback:
                                    progress_callback(downloaded_size, total_size)

                except OSError as e:
                    logger.error(f"failed to write file: {e}")
                    raise DownloadError(f"failed to write to {dest_path}: {e}") from e

                checksum = md5_hash.hexdigest() if md5_hash else None

                logger.info(f"download complete: {downloaded_size / (1024 * 1024):.2f} MB")
                return DownloadResult(url=url, destination=dest_path, size_bytes=downloaded_size, checksum=checksum)
        else:
            download_files = multiple_url_download(
                url=url,
                destination=destination,
                session=self._session,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            return multiple_download_result(url, download_files)

    def download_bytes(self, url: str) -> bytes:
        """download file content as bytes (in-memory)."""
        self._validate_url(url)

        logger.info(f"downloading to memory: {url}")

        try:
            response = self._session.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"download failed: {e}")
            raise DownloadError(f"failed to download {url}: {e}") from e

        logger.info(f"downloaded {len(response.content)} bytes")
        return response.content

    def _is_directory(self, url: str) -> bool:
        """check if url points to a directory"""
        try:
            data = self._directory_contents_json(url)

            if isinstance(data, dict) and "items" in data:
                return True

            return False

        except (requests.exceptions.RequestException, ValueError):
            return False

    def _directory_contents_json(self, url: str) -> dict:
        """send json query to url"""

        # change url to data.ceda... for json query
        parsed_url = urlparse(url)
        if parsed_url.netloc == "dap.ceda.ac.uk":
            url = f"https://data.ceda.ac.uk{parsed_url.path}"
        return self._session.get(f"{url}?json").json()

    def _recursive_download(self, url, destination, calculate_checksum, progress_callback) -> list[DownloadResult]:
        """download all files in a directory"""

        file_list = []
        contents = self._directory_contents_json(url)
        for item in contents["items"]:
            item_url = urljoin(url, item["path"])
            dest_path = destination / item["name"]
            result = self.download(
                url=item_url,
                destination=dest_path,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            file_list.append(result)

        return file_list
