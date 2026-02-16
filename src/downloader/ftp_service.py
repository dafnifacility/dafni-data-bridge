import os
from ftplib import FTP, error_perm
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

from downloader.base import BaseDownloader
from downloader.download_utils import (
    download_local,
    extract_filename,
    logger,
    multiple_download_result,
    multiple_url_download,
    multiple_urls_split,
    resolve_destination,
)
from downloader.models import DownloadResult, ProgressCallback


class FTPDownloader(BaseDownloader):
    """
    FTP implementation of the file downloader.

    This class uses a persistent session to handle downloads, supporting chunked transfers and progress tracking.

    Args:
        session: A requests.Sessions object

    """

    DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "8192"))

    def __init__(self, session: FTP, chunk_size: int | None = None):
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self._chunk_size = chunk_size
        if chunk_size <= 0:
            raise ValueError("chunk size must be positive")
        self._session = session

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
            parsed = urlparse(url)
            dest_path = resolve_destination(url, destination)

            if self._is_directory(parsed.path):
                directory_download = self._recursive_download(url, dest_path, calculate_checksum, progress_callback)
                return multiple_download_result(url, directory_download)
            else:
                total_size = self._session.size(parsed.path)
                if total_size:
                    logger.info(f"file size: {total_size / (1024 * 1024):.2f} MB")

                logger.info(f"starting download: {url}")
                logger.info(f"destination: {dest_path}")

                return download_local(
                    url=url,
                    dest_path=dest_path,
                    response=self._session,
                    total_size=total_size,
                    calculate_checksum=calculate_checksum,
                    progress_callback=progress_callback,
                    chunk_size=self._chunk_size,
                    parsed_path=parsed.path,
                )
        else:
            download_files = multiple_url_download(
                url=url,
                destination=destination,
                session=self._session,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            return multiple_download_result(url, download_files)

    def _is_directory(self, path: str):
        """check if url points to a directory"""
        try:
            self._session.cwd(path)
            logger.info(f"{path} is a directory")
            return True
        except error_perm:
            return False

    def _get_directory_contents(self, url: str) -> dict:
        """gets all directory contents from ftp server"""
        parsed = urlparse(url)
        items_url = []

        for file in self._session.nlst(parsed.path):
            items_url.append(urljoin(url, file))

        return items_url

    def _recursive_download(
        self,
        url: str,
        destination: str,
        calculate_checksum: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> list[DownloadResult]:
        """download all files from directory"""
        file_list = []
        contents = self._get_directory_contents(url)

        self._session.voidcmd("TYPE I")

        for item_url in contents:
            filename = extract_filename(item_url)

            dest_path = destination / filename
            result = self.download(
                url=item_url,
                destination=dest_path,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            file_list.append(result)

        return file_list
