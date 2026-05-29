from __future__ import annotations
from pathlib import Path
import logging
from urllib.parse import urlparse
from typing import Optional
import os

from dataset_download_tool.downloader.download_utils import extract_filename
from dataset_download_tool.exceptions import ValidationError

logger = logging.getLogger(__name__)

ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")

def resolve_destination(url: str, destination: Optional[str | Path], storage: str) -> Path:
    """Resolve the final destination path for a download."""
    filename = extract_filename(url)

    match storage:
        case "local":
                if destination is None:
                    return Path.cwd() / filename
                if str(destination).startswith(("https://", "http://", "s3://")):
                    logger.error(f"Local storage selected but given remote URL: {destination}")
                    raise ValidationError("Please select correct storage location!")
                
                dest_path = Path(destination)
                # if destination is a directory, append filename
                if dest_path.is_dir() or str(destination).endswith(os.sep):
                    dest_path.mkdir(parents=True, exist_ok=True)
                    return dest_path / filename

                return dest_path
        
        case "s3":
            parsed = urlparse(destination)

            if destination.startswith("s3://"):
                raise ValidationError("S3 endpoint wrong format please use aws format: https://[BUCKET].[S3 ENDPOINT]/DIR")

            subdir = parsed.path.lstrip("/")
            if not subdir:
                raise ValidationError(
                    f"S3 destination '{destination}' is missing a directory. "
                    "Please provide a destination in the format: "
                    "https://[BUCKET].[S3 ENDPOINT]/DIR (e.g. https://mybucket.s3.example.com/mydir)"
                )
            bucket = parsed.netloc.split(".")[0]
            endpoint = parsed.scheme + "://" + parsed.netloc.replace(f"{bucket}.", "")
            key = f"{subdir}/{filename}"
            return {"endpoint": endpoint, "bucket": bucket, "key": key}

        case "blob":
            parsed = urlparse(destination)
            if destination.startswith(("https://", "http://")):

                bucket = parsed.netloc.split(".")[0]
                bare_host = parsed.netloc.replace(f"{bucket}.", "")
                endpoint = f"{parsed.scheme}://{bare_host}"

                subdir = parsed.path.lstrip("/")
                if ACCOUNT_NAME and subdir.startswith(f"{ACCOUNT_NAME}/"):
                    subdir = subdir[len(ACCOUNT_NAME) + 1:]
                
                if not subdir:
                    raise ValidationError(
                        f"Azure destination '{destination}' is missing a directory. "
                        "Please provide a destination in the format: "
                        "https://[CONTAINER].[AZURE URL]/[AZURE_ACCOUNT_NAME]/DIR (e.g. https://ddtesting.blob.core.windows.net/devaccount1/mydir)"
                    )
        
                key = f"{subdir}{filename}"
                print("endpoint",endpoint,"bucket", bucket, "key", key)
                return {"endpoint": endpoint, "bucket": bucket, "key": key}
            else:
                raise ValidationError("Azure endpoint url wrong format please use aws format: https://[CONTAINER].[AZURE URL]/[AZURE_ACCOUNT_NAME]/DIR")

def append_bucket_url(destination: dict) -> str:
    """Append bucket name to s3 endpoint for recursive downloads"""
    parsed = urlparse(destination["endpoint"])
    return f"{parsed.scheme}://{destination["bucket"]}.{parsed.netloc}/{destination['key']}"
