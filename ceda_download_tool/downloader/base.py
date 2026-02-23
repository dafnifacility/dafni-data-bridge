from abc import ABC, abstractmethod
from typing import Optional

from ceda_download_tool.downloader.models import DownloadResult, ProgressCallback


class BaseDownloader(ABC):
    """
    Abstract base class for all downloader implementations.

    Example:
        downloader = get_downloader(url, session)

        result = downloader.download(url, destination="/path/to/file.nc")   # download to specific path
        result = downloader.download(url, destination="/download/dir/")  # download to directory (auto-detect filename)

        def on_progress(downloaded, total):                                 # with progress callback
            print(f"{downloaded}/{total} bytes")
        result = downloader.download(url, progress_callback=on_progress)
    """

    @abstractmethod
    def download(
        self,
        url: str,
        destination: str,
        progress_callback: Optional[ProgressCallback] = None,
        calculate_checksum: bool = False,
    ) -> DownloadResult:
        """download file from a given url"""
        pass
