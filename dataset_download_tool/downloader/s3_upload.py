import hashlib
import logging
import os
from typing import Iterable, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client as S3ClientBoto3

from dataset_download_tool.downloader.models import ProgressCallback
from dataset_download_tool.exceptions import AuthError, BucketNotFoundError

logger = logging.getLogger(__name__)

CONFIG = Config(request_checksum_calculation="when_required", response_checksum_validation="when_required")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")


class S3Client:
    """S3 file uploader class

    This class opens an S3 client and uploads chunks

    Args:
        s3_endpoint: str of endpoint to s3

    """

    CHUNK_SIZE = 5 * 1024 * 1024

    def __init__(self, s3_endpoint):
        self._client: S3ClientBoto3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name="us",
            config=CONFIG,
        )

    def upload_to_s3(
        self,
        chunk_iter: Iterable[bytes],
        bucket: str,
        key: str,
        total_size: float = 0,
        calculate_checksum: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict:
        md5_hash = hashlib.md5() if calculate_checksum else None
        downloaded_size = 0

        try:
            part_upload_init = self._client.create_multipart_upload(Bucket=bucket, Key=key)
            upload_id = part_upload_init["UploadId"]
            parts_list = []
            part_num = 1
            uploaded_size = 0
            buffer = bytearray()

            for chunk in chunk_iter:
                buffer.extend(chunk)
                uploaded_size += len(chunk)

                if md5_hash:
                    md5_hash.update(chunk)

                if len(buffer) >= self.CHUNK_SIZE:
                    etag = self._upload_part(bucket, key, upload_id, part_num, bytes(buffer))
                    parts_list.append({"PartNumber": part_num, "ETag": etag})
                    part_num += 1
                    buffer.clear()

                if progress_callback:
                    progress_callback(downloaded_size, total_size)

            if buffer:
                etag = self._upload_part(bucket, key, upload_id, part_num, bytes(buffer))
                parts_list.append({"PartNumber": part_num, "ETag": etag})

            result = self._client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts_list},
            )

            checksum = md5_hash.hexdigest() if md5_hash else None

            return {
                "destination": result["Location"],
                "size_bytes": uploaded_size,
                "checksum": checksum,
            }
        except self._client.exceptions.NoSuchBucket:
            logger.error("bucket not found")
            raise BucketNotFoundError(
                f"failed to upload to bucket: {bucket}" "please use aws format: https://[BUCKET].[S3 ENDPOINT]/DIR"
            )
        except ClientError as e:
            logger.error(f"client error {e}")
            raise AuthError(f"Cannot access {bucket}: {e}")

    def _upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes,
    ) -> str:
        response = self._client.upload_part(
            Bucket=bucket,
            Key=key,
            PartNumber=part_number,
            UploadId=upload_id,
            Body=data,
        )
        return response["ETag"]
