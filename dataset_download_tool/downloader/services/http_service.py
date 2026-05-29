from urllib.parse import urljoin, urlparse

import requests

from dataset_download_tool.downloader.base import BaseDownloader
from dataset_download_tool.downloader.download_utils import (
    logger,
)
from dataset_download_tool.downloader.models import DownloadResult, ProgressCallback
from dataset_download_tool.exceptions import AuthenticationRequiredError, DownloadError, HTTPError
from dataset_download_tool.storage_selector.selector_utils import append_bucket_url


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
        storage
    ) -> list[DownloadResult]:
        """Download all files in a directory"""
        file_list = []
        contents = self._directory_contents(url)
        if isinstance(destination, dict):
            destination = append_bucket_url(destination)
        for item in contents["items"]:
            item_url = urljoin(url, item["path"])
            result = self.download(
                url=item_url,
                destination=destination,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
                storage=storage
            )
            file_list.append(result)

        return file_list

    def _stream(self, url: str):
        """Create data stream to call files in chunks.

        Returns:
            generator: A generator that yields chunks of data
            int: total number of bytes

        """

        try:
            response = self._session.get(url, stream=True)
            response.raise_for_status()

            # Check if response is HTML (case-insensitive, handle missing header)
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                # Likely an authentication page or error page
                raise AuthenticationRequiredError(
                    f"File not accessible at {url}. "
                    f"Received HTML response (status {response.status_code}). "
                    "Please check your authentication or verify the file URL.",
                    status_code=response.status_code,
                    url=url
                )

        except requests.HTTPError as e:
            # Provide more detailed HTTP error information
            status_code = None
            if e.response is not None:
                status_code = getattr(e.response, 'status_code', None)
            status_str = str(status_code) if status_code is not None else "unknown"
            logger.error(
                f"HTTP error {status_str} while downloading {url}: {e}\n"
                "Please ensure you have access to the file and the URL is correct."
            )
            raise HTTPError(
                f"Failed to download {url}: HTTP {status_str} - {e}",
                status_code=status_code,
                url=url
            ) from e

        except requests.RequestException as e:
            logger.error(
                f"Download request failed for {url}: {e}\n"
                "Please ensure you have network connectivity and access to the file."
            )
            raise DownloadError(f"Failed to download {url}: {e}") from e

        total_size = int(response.headers.get("content-length", 0)) or None

        def generator():
            for chunk in response.iter_content(chunk_size=self._chunk_size):
                if chunk:
                    yield chunk

        return generator(), total_size
