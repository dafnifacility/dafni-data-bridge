import hashlib
import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from exceptions import DownloadError, ValidationError

from downloader.models import DownloadResult, ProgressCallback

logger = logging.getLogger(__name__)


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

    if isinstance(destination, str):
        parsed = urlparse(destination)
        if destination.startswith("https://"):
            path = parsed.path.split("/")
            bucket = parsed.netloc.split(".")[0]
            endpoint = "https://" + parsed.netloc.replace(f"{bucket}.", "")
            key = f"{path[1]}/{filename}"
            return {"endpoint": endpoint, "bucket": bucket, "key": key}

    if destination is None:
        return Path.cwd() / filename

    dest_path = Path(destination)

    # if destination is a directory, append filename
    if dest_path.is_dir() or str(destination).endswith(os.sep):
        dest_path.mkdir(parents=True, exist_ok=True)

        return dest_path / filename

    return dest_path


def download_local(
    url: str,
    dest_path: str,
    response,
    total_size,
    calculate_checksum,
    progress_callback,
    chunk_size,
    parsed_path: Optional[str] = None,
) -> DownloadResult:
    md5_hash = hashlib.md5() if calculate_checksum else None
    downloaded_size = 0

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            if url.startswith("https://"):
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if md5_hash:
                            md5_hash.update(chunk)

                        if progress_callback:
                            progress_callback(downloaded_size, total_size)
            else:

                def chunk_download(data):
                    nonlocal downloaded_size
                    f.write(data)
                    downloaded_size += len(data)
                    md5_hash.update(data)

                    if progress_callback:
                        progress_callback(downloaded_size, total_size)

                response.retrbinary(f"RETR {parsed_path}", chunk_download, blocksize=chunk_size)

    except OSError as e:
        logger.error(f"failed to write file: {e}")
        raise DownloadError(f"failed to write to {dest_path}: {e}") from e

    checksum = md5_hash.hexdigest() if md5_hash else None
    logger.info(f"download complete: {downloaded_size / (1024 * 1024):.2f} MB")

    return DownloadResult(url=url, destination=dest_path, size_bytes=downloaded_size, checksum=checksum)


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
