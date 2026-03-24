from urllib.parse import urljoin, urlparse

import requests

from dataset_download_tool.downloader.base import BaseDownloader
from dataset_download_tool.downloader.download_utils import (
    append_bucket_url,
    logger,
)
from dataset_download_tool.downloader.models import DownloadResult, ProgressCallback
from dataset_download_tool.exceptions import DownloadError


class HTTPDownloader(BaseDownloader):
    """Base HTTP/S implementation of the file downloader.

    This class uses a persistent session to handle logic, checking url contents and stream data.

    Args:
        session: A requests.Sessions object

    """

    def __init__(self, session: requests.Session):
        super().__init__(session)

    def _is_directory(self, url: str) -> bool:
        """Check if url points to a directory"""
        try:
            data = self._directory_contents(url)

            if isinstance(data, dict) and "items" in data:
                return True

            return False

        except (requests.exceptions.RequestException, ValueError):
            return False

    def _directory_contents(self, url: str) -> dict:
        """Send json query to url"""
        # change url to data.ceda... for json query
        parsed_url = urlparse(url)
        if parsed_url.netloc == "dap.ceda.ac.uk":
            url = f"https://data.ceda.ac.uk{parsed_url.path}"
        return self._session.get(f"{url}?json").json()

    def _recursive_download(
        self,
        url: str,
        destination: str,
        calculate_checksum: bool,
        progress_callback: ProgressCallback,
    ) -> list[DownloadResult]:
        """Download all files in a directory"""
        file_list = []
        contents = self._directory_contents(url)
        if isinstance(destination, dict):
            destination = append_bucket_url(destination)
        for item in contents["items"]:
            item_url = urljoin(url, item["path"])
            dest_path = f"{destination}/{item["name"]}"
            result = self.download(
                url=item_url,
                destination=dest_path,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            file_list.append(result)

        return file_list

    def _stream(self, url: str):
        """Create data stream to call files in chunks.

        Returns:
            generator: A generator that yields chunks of data
            int: total numver of bytes

        """

        try:
            response = self._session.get(url, stream=True)
            response.raise_for_status()
            if response.headers["Content-Type"] == "text/html; charset=utf-8":
                raise DownloadError("File not accesssible! Check login or file URL")
        except requests.RequestException as e:
            logger.error(
                f"download request failed: {e} \nNOTE:"
                'If you are downloading a directory please ensure url ends with "/" e.g. https://url.com/dir'
            )
            raise DownloadError(f"failed to download {url}: {e}") from e

        total_size = int(response.headers.get("content-length", 0)) or None

        def generator():
            for chunk in response.iter_content(chunk_size=self._chunk_size):
                if chunk:
                    yield chunk

        return generator(), total_size
