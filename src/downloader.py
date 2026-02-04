import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import unquote, urljoin, urlparse

import requests
from exceptions import DownloadError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    url: str | list[str]
    destination: Path | list[Path]
    size_bytes: int
    checksum: Optional[str] = None

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)


ProgressCallback = Callable[[int, int], None]


class Downloader:
    """
    downloads files from with progress tracking, supports streaming downloads,
    automatic filename detection, checksum calculation, and progress callbacks

    Example:
        downloader = Downloader(session)

        result = downloader.download(url, destination="/path/to/file.nc")   # download to specific path
        result = downloader.download(url, destination="/download/dir/")  # download to directory (auto-detect filename)

        def on_progress(downloaded, total):                                 # with progress callback
            print(f"{downloaded}/{total} bytes")
        result = downloader.download(url, progress_callback=on_progress)
    """

    CEDA_DAP_HOST = os.getenv("CEDA_DAP_HOST", "dap.ceda.ac.uk")
    DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "8192"))

    def __init__(self, session: requests.Session, chunk_size: int | None = None):
        """
        Args:
            session: configured requests session with auth.
            chunk_size: size of chunks for streaming downloads.
        """
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

        url = self._multiple_urls_split(url)

        if isinstance(url, str):

            self._validate_url(url)
            dest_path = self._resolve_destination(url, destination)

            if self._is_directory(url):

                logger.info(f"Downloading directory: {url}")
                directory_download = self._recursive_download(url, dest_path)
                
                return self._multiple_download_result(url, directory_download)
            
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
            
            download_files = self._multiple_url_download(url, destination)
            return self._multiple_download_result(url, download_files)
        
    def download_bytes(self, url: str) -> bytes:
        """
        download file content as bytes (in-memory).

        Args:
            url: url to download from.

        Returns:
            File content as bytes.

        Raises:
            ValidationError: if url is invalid.
            DownloadError: if download fails.
        """
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

    def _validate_url(self, url: str) -> None:
        if not url:
            raise ValidationError("url cannot be empty")

        if not isinstance(url, str):
            raise ValidationError("url must be a string")

        parsed = urlparse(url)

        if not parsed.scheme:
            raise ValidationError("url must include scheme (http/https)")

        if parsed.scheme not in ("http", "https"):
            raise ValidationError(f"unsupported url scheme: {parsed.scheme}")

        if not parsed.netloc:
            raise ValidationError("url must include host")

    def _resolve_destination(self, url: str, destination: Optional[str | Path]) -> Path:
        """resolve the final destination path for a download."""
        filename = self._extract_filename(url)

        if destination is None:
            return Path.cwd() / filename

        dest_path = Path(destination)

        # if destination is a directory, append filename
        if dest_path.is_dir() or str(destination).endswith(os.sep):
            dest_path.mkdir(parents=True, exist_ok=True)
            return dest_path / filename

        return dest_path

    @staticmethod
    def _extract_filename(url: str) -> str:
        """extract filename from url."""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path)

        if not filename:
            raise ValidationError(f"cannot extract filename from url: {url}")

        return filename

    def _is_directory(self, url: str) -> bool:
        """check if url points to a directory"""
        try:
            data = self._directory_contents_json(url)
            
            if isinstance(data, dict) and 'items' in data:
                return True      
                      
            return False

        except (requests.exceptions.RequestException, ValueError):
            return False
        
    @staticmethod
    def _multiple_urls_split(url: str) -> list[str] | str:
        """split multiple urls into list"""
        url = url.split(",")
        if len(url) > 1:
            logger.info(f"Number of files to download: {len(url)}")
            return url
        else:
            return str(url[0])
    
    def _multiple_url_download(self, url: str, destination:Path) -> list[DownloadResult]:
        """download all files from a list"""
        download_list = []
        for file_url in url:
            result = self.download(file_url, destination)
            download_list.append(result)

        return download_list

    def _multiple_download_result(self, url: list, results: list[DownloadResult]) -> DownloadResult:
        """return results of multiple files installed"""
        total_files = []
        total_size = 0
        for download_result in results:
            total_files.append(download_result.destination)
            total_size += download_result.size_bytes
        
        return DownloadResult(url=url, destination=total_files, size_bytes=total_size, checksum=results[0].checksum)

    def _directory_contents_json(self, url:str) -> dict:
        """send json query to url"""

        # change url to data.ceda... for json query
        parsed_url = urlparse(url)
        if parsed_url.netloc == "dap.ceda.ac.uk":
            url = f'https://data.ceda.ac.uk{parsed_url.path}'
        return self._session.get(f'{url}?json').json()
    
    def _recursive_download(self, url:str, destination:Path) -> list[DownloadResult]:
        """
        download all files in a directory

        Args:
            url: url to download from.
            destination: path to download to

        Returns:
            list of files with DownloadResult
        """

        file_list = []
        contents = self._directory_contents_json(url)
        for item in contents['items']:
            
            item_url = urljoin(url, item['path'])
            dest_path = destination / item['name']
            result = self.download(item_url, dest_path)
            file_list.append(result)

        return file_list

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
