import logging
import os
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import unquote, urlparse

from exceptions import ValidationError

from downloader.models import DownloadResult, ProgressCallback

logger = logging.getLogger(__name__)


def create_progress_logger(log_interval_mb: float = 10.0) -> ProgressCallback:
    """
    create a progress callback that logs download progress.

    Args:
        log_interval_mb: log progress every N megabytes.

    Returns:
        progress callback function.
    """
    last_logged_mb = [0.0]

    def log_progress(downloaded: int, total: int) -> None:
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024) if total else 0

        if downloaded_mb - last_logged_mb[0] >= log_interval_mb:
            if total_mb > 0:
                percent = (downloaded / total) * 100
                logger.info(f"progress: {downloaded_mb:.1f}/{total_mb:.1f} mb ({percent:.1f}%)")
            else:
                logger.info(f"progress: {downloaded_mb:.1f} mb downloaded")

            last_logged_mb[0] = downloaded_mb

    return log_progress


def create_progress_bar(desc: str = "downloading") -> tuple[ProgressCallback, Callable[[], None]]:
    """
    create a simple console progress bar.

    Args:
        desc: description to show before progress bar.

    Returns:
        tuple of (progress_callback, close_function).
    """
    state = {"last_percent": -1}

    def show_progress(downloaded: int, total: int) -> None:
        if total <= 0:
            return

        percent = int((downloaded / total) * 100)

        if percent != state["last_percent"]:
            bar_length = 40
            filled = int(bar_length * downloaded / total)
            bar = "=" * filled + "-" * (bar_length - filled)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)

            print(f"\r{desc}: [{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} mb)", end="", flush=True)
            state["last_percent"] = percent

    def close() -> None:
        print()  # new line after progress bar

    return show_progress, close


def extract_filename(url: str) -> str:
    """extract filename from url."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)

    if not filename:
        raise ValidationError(f"cannot extract filename from url: {url}")

    return filename


def resolve_destination(url: str, destination: Optional[str | Path]) -> Path:
    """resolve the final destination path for a download."""

    filename = extract_filename(url)

    if destination is None:
        return Path.cwd() / filename

    dest_path = Path(destination)

    # if destination is a directory, append filename
    if dest_path.is_dir() or str(destination).endswith(os.sep):
        dest_path.mkdir(parents=True, exist_ok=True)

        return dest_path / filename

    return dest_path


def multiple_urls_split(url: str) -> list[str] | str:
    """split multiple urls into list"""
    url = [u.strip() for u in url.split(",") if u.strip()]
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
    session=None,
) -> list[DownloadResult]:
    """download all files from list of"""
    from downloader import get_downloader

    download_list = []
    for file_url in url:
        downloader = get_downloader(file_url, session)
        result = downloader.download(
            url=file_url,
            destination=destination,
            calculate_checksum=calculate_checksum,
            progress_callback=progress_callback,
        )
        download_list.append(result)

    return download_list


def multiple_download_result(url: list, results: list[DownloadResult]) -> DownloadResult:
    """return results of multiple files installed"""
    total_files = []
    total_size = 0
    for download_result in results:
        total_files.append(download_result.destination)
        total_size += download_result.size_bytes

    return DownloadResult(url=url, destination=total_files, size_bytes=total_size, checksum=results[0].checksum)
