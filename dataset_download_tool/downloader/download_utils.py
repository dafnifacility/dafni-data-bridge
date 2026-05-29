import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from dataset_download_tool.downloader.models import DownloadResult, ProgressCallback
from dataset_download_tool.exceptions import ValidationError

logger = logging.getLogger(__name__)


def extract_filename(url: str) -> str:
    """Extract filename from url."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)

    if not filename:
        return ""

    return filename

def multiple_urls_split(url: str) -> list[str] | str:
    """Split multiple urls into list"""
    url = [u.strip() for u in url.split("|") if u.strip()]
    if len(url) > 1:
        logger.info(f"Number of files to download: {len(url)}")
        return url
    else:
        return str(url[0])


def multiple_url_download(
    url: list[str],
    destination: str,
    calculate_checksum: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
    storage: int = 0,
    session=None,
) -> list[DownloadResult]:
    """Download all files from list of"""
    from dataset_download_tool.downloader import get_downloader

    download_list = []
    for file_url in url:
        downloader = get_downloader(file_url, session)
        result = downloader.download(
            url=file_url,
            destination=destination,
            calculate_checksum=calculate_checksum,
            progress_callback=progress_callback,
            storage=storage
        )
        download_list.append(result)

    return download_list


def multiple_download_result(url: list, results: list[DownloadResult]) -> DownloadResult:
    """Return results of multiple files installed"""
    total_files = []
    total_size = 0
    for download_result in results:
        total_files.append(download_result.destination)
        total_size += download_result.size_bytes

    return DownloadResult(url=url, destination=total_files, size_bytes=total_size, checksum=results[0].checksum)
