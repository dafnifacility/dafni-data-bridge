from ftplib import FTP, error_perm
from typing import Optional
from urllib.parse import urljoin, urlparse

from dataset_download_tool.downloader.base import BaseDownloader
from dataset_download_tool.downloader.download_utils import (
    extract_filename,
    logger,
)
from dataset_download_tool.downloader.models import DownloadResult, ProgressCallback
from dataset_download_tool.exceptions import ValidationError
from dataset_download_tool.storage_selector.selector_utils import append_bucket_url


class FTPDownloader(BaseDownloader):
    """FTP implementation of the file downloader.

    This class uses a persistent session to handle downloads, supporting chunked transfers and progress tracking.

    Args:
        session: A FTP object

    """

    def __init__(self, session: FTP):
        super().__init__(session)

    def _is_directory(self, url: str):
        """Check if url points to a directory"""
        parsed = urlparse(url)
        try:
            self._session.cwd(parsed.path)
            logger.info(f"{parsed.path} is a directory")
            return True
        except error_perm:
            return False

    def _get_directory_contents(self, url: str) -> dict:
        """Gets all directory contents from ftp server"""
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
        storage: int = 0,
    ) -> list[DownloadResult]:
        """Download all files from directory"""
        file_list = []
        contents = self._get_directory_contents(url)

        self._session.voidcmd("TYPE I")
        if isinstance(destination, dict):
            destination = append_bucket_url(destination)
        for item_url in contents:
            filename = extract_filename(item_url)
            dest_path = f"{str(destination).strip("/")}"
            result = self.download(
                url=item_url,
                destination=dest_path,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
                storage=storage
            )
            file_list.append(result)

        return file_list

    def _stream(self, url: str):
        parsed = urlparse(url)
        try:
            total_size = self._session.size(parsed.path)

            def generator():
                self._session.voidcmd("TYPE I")
                with self._session.transfercmd(f"RETR {parsed.path}") as conn:
                    while True:
                        chunk = conn.recv(self._chunk_size)
                        if not chunk:
                            break
                        yield chunk
                self._session.voidresp()

            return generator(), total_size
        except error_perm as e:
            logger.error(f"Cannot access {url}")
            raise ValidationError(f"Cannot access {url}: {e}")
