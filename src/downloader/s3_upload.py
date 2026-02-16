import ftplib
import hashlib
import logging
import os
from typing import Optional

import boto3
import botocore
import requests
from botocore.config import Config
from exceptions import BucketNotFoundError
from mypy_boto3_s3 import S3Client as S3ClientBoto3

from downloader.models import ProgressCallback

logger = logging.getLogger(__name__)

CONFIG = Config(request_checksum_calculation="when_required", response_checksum_validation="when_required")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")


class S3Client:
    """
    S3 file uploader class

    This class opens an S3 client and uploads chunks

    Args:
        s3_endpoint: str of endpoint to s3
    """

    def __init__(self, s3_endpoint):
        self._client: S3ClientBoto3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name="us",
            config=CONFIG,
        )

    # TODO method size too long refactor client class to handle download logic
    def upload_to_s3(
        self,
        response: ftplib.FTP | requests.Session,
        bucket: str,
        object: str,
        chunk_size: int,
        calculate_checksum: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
        total_size: float = 0,
        parsed_path: Optional[str] = None,
    ) -> dict:
        md5_hash = hashlib.md5() if calculate_checksum else None
        downloaded_size = 0
        try:
            part_upload_init = self._client.create_multipart_upload(Bucket=bucket, Key=object)
            upload_id = part_upload_init["UploadId"]
            parts_list = []
            part_num = 1

            match response:
                case requests.models.Response():
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        part_upload = self._client.upload_part(
                            Body=chunk, Bucket=bucket, Key=object, PartNumber=part_num, UploadId=upload_id
                        )

                        if md5_hash:
                            md5_hash.update(chunk)

                        if progress_callback:
                            progress_callback(downloaded_size, total_size)

                        parts_list.append({"PartNumber": part_num, "ETag": part_upload["ETag"]})
                        part_num += 1

                case ftplib.FTP():
                    buffer = bytearray()

                    def chunk_download(data):
                        nonlocal downloaded_size, part_num, buffer
                        buffer.extend(data)
                        downloaded_size += len(data)
                        md5_hash.update(data)
                        if len(buffer) >= chunk_size:
                            part_upload = self._client.upload_part(
                                Body=bytes(buffer), Bucket=bucket, Key=object, PartNumber=part_num, UploadId=upload_id
                            )
                            parts_list.append({"PartNumber": part_num, "ETag": part_upload["ETag"]})
                            part_num += 1
                            buffer.clear()

                        if progress_callback:
                            progress_callback(downloaded_size, total_size)

                    response.retrbinary(f"RETR {parsed_path}", chunk_download, blocksize=chunk_size)
                    if len(buffer) > 0:
                        part_upload = self._client.upload_part(
                            Body=bytes(buffer), Bucket=bucket, Key=object, PartNumber=part_num, UploadId=upload_id
                        )
                        parts_list.append({"PartNumber": part_num, "ETag": part_upload["ETag"]})

            s3_result = self._client.complete_multipart_upload(
                Bucket=bucket, Key=object, UploadId=upload_id, MultipartUpload={"Parts": parts_list}
            )
            checksum = md5_hash.hexdigest() if md5_hash else None
            logger.info(f"upload complete: {downloaded_size / (1024 * 1024):.2f} MB")

            return {"destination": s3_result["Location"], "size_bytes": downloaded_size, "checksum": checksum}

        except botocore.exceptions.ClientError as error:
            error_response = error.response["Error"]["Code"]

            if error_response == "NoSuchBucket":
                logger.error(f"Upload failed {error_response}")
                raise BucketNotFoundError(f"Failed to upload to bucket {bucket}: {error_response}") from error
