import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from ceda_download_tool.downloader.models import DownloadResult, ProgressCallback
from ceda_download_tool.exceptions import ValidationError

logger = logging.getLogger(__name__)


def extract_filename(url: str) -> str:
    """Extract filename from url."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)

    if not filename:
        return ""

    return filename


def resolve_destination(url: str, destination: Optional[str | Path]) -> Path:
    """Resolve the final destination path for a download."""
    filename = extract_filename(url)

    if isinstance(destination, str):
        parsed = urlparse(destination)
        if destination.startswith("https://"):
            path = parsed.path.split("/")
            bucket = parsed.netloc.split(".")[0]
            endpoint = "https://" + parsed.netloc.replace(f"{bucket}.", "")
            key = f"{path[1]}/{filename}"
            return {"endpoint": endpoint, "bucket": bucket, "key": key}

        if destination.startswith("s3://"):
            raise ValidationError("S3 endpoint wrong format please use aws format: https://[BUCKET].[S3 ENDPOINT]/DIR")

    if destination is None:
        return Path.cwd() / filename

    dest_path = Path(destination)
    # if destination is a directory, append filename
    if dest_path.is_dir() or str(destination).endswith(os.sep):
        dest_path.mkdir(parents=True, exist_ok=True)

        return dest_path / filename

    return dest_path


def append_bucket_url(destination: dict) -> str:
    """Append bucket name to s3 endpoint for recursive downloads"""
    parsed = urlparse(destination["endpoint"])
    return f"https://{destination["bucket"]}.{parsed.netloc}/{destination['key']}"


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
    session=None,
) -> list[DownloadResult]:
    """Download all files from list of"""
    from ceda_download_tool.downloader import get_downloader

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
    """Return results of multiple files installed"""
    total_files = []
    total_size = 0
    for download_result in results:
        total_files.append(download_result.destination)
        total_size += download_result.size_bytes

    return DownloadResult(url=url, destination=total_files, size_bytes=total_size, checksum=results[0].checksum)
