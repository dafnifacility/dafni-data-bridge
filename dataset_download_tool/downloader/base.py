import hashlib
import os
from abc import ABC, abstractmethod
from ftplib import FTP
from pathlib import Path
from typing import Iterable, Optional

import requests
from paramiko import SSHClient

from dataset_download_tool.downloader.download_utils import (
    logger,
    multiple_download_result,
    multiple_url_download,
    multiple_urls_split,
    resolve_destination,
)
from dataset_download_tool.downloader.models import DownloadResult, ProgressCallback
from dataset_download_tool.downloader.s3_upload import S3Client
from dataset_download_tool.exceptions import ValidationError


class BaseDownloader(ABC):
    """Abstract base class for all downloader implementations.

    Example:
        downloader = get_downloader(url, session)

        result = downloader.download(url, destination="/path/to/file.nc")   # download to specific path
        result = downloader.download(url, destination="/download/dir/")  # download to directory (auto-detect filename)

        def on_progress(downloaded, total):                                 # with progress callback
            print(f"{downloaded}/{total} bytes")
        result = downloader.download(url, progress_callback=on_progress)

    """

    DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "8192"))

    @abstractmethod
    def __init__(self, session: FTP | requests.Session | SSHClient, chunk_size: int | None = None):
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self._chunk_size = chunk_size
        if chunk_size <= 0:
            raise ValueError("chunk size must be positive")
        self._session = session

    @abstractmethod
    def _stream(self, url: str) -> tuple[Iterable[bytes], Optional[int]]:
        pass

    @abstractmethod
    def _is_directory(self, url: str) -> bool:
        pass

    @abstractmethod
    def _recursive_download(self, url, destination, calculate_checksum, progress_callback) -> list[DownloadResult]:
        pass

    def _write_file(
        self,
        url: str,
        dest_path: Path,
        chunk_iter: Iterable[bytes],
        total_size: Optional[int],
        progress_callback: Optional[ProgressCallback],
        calculate_checksum: bool,
    ) -> DownloadResult:
        md5_hash = hashlib.md5() if calculate_checksum else None
        downloaded_size = 0

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error(f"Could not create file at {dest_path}")
            raise ValidationError(f"Enter valid path: {e}")

        with open(dest_path, "wb") as f:
            for chunk in chunk_iter:
                f.write(chunk)
                downloaded_size += len(chunk)

                if md5_hash:
                    md5_hash.update(chunk)

                if progress_callback:
                    progress_callback(downloaded_size, total_size)

        checksum = md5_hash.hexdigest() if md5_hash else None

        return DownloadResult(
            url=url,
            destination=dest_path,
            size_bytes=downloaded_size,
            checksum=checksum,
        )

    def s3_upload(
        self, url, chunk_iter, dest_path, calculate_checksum, progress_callback, total_size
    ) -> DownloadResult:
        s3_uploader = S3Client(s3_endpoint=dest_path["endpoint"])
        result = s3_uploader.upload_to_s3(
            chunk_iter=chunk_iter,
            bucket=dest_path["bucket"],
            key=dest_path["key"],
            calculate_checksum=calculate_checksum,
            progress_callback=progress_callback,
            total_size=total_size,
        )
        return DownloadResult(
            url=url,
            destination=result["destination"],
            size_bytes=result["size_bytes"],
            checksum=result["checksum"],
        )

    def download(
        self,
        url: str,
        destination: Optional[str | Path] = None,
        progress_callback: Optional[ProgressCallback] = None,
        calculate_checksum: bool = False,
    ) -> DownloadResult:
        """Args:
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

                chunk_iter, total_size = self._stream(url)
                if isinstance(dest_path, Path):
                    if total_size:
                        logger.info(f"file size: {total_size / (1024 * 1024):.2f} MB")
                    return self._write_file(
                        url=url,
                        dest_path=dest_path,
                        chunk_iter=chunk_iter,
                        total_size=total_size,
                        calculate_checksum=calculate_checksum,
                        progress_callback=progress_callback,
                    )

                if isinstance(dest_path, dict):
                    return self.s3_upload(
                        url=url,
                        chunk_iter=chunk_iter,
                        dest_path=dest_path,
                        calculate_checksum=calculate_checksum,
                        progress_callback=progress_callback,
                        total_size=total_size,
                    )

        if isinstance(url, list):
            download_files = multiple_url_download(
                url=url,
                destination=destination,
                session=self._session,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            return multiple_download_result(url, download_files)
