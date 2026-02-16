import hashlib
import logging

import boto3
import botocore
import requests
from botocore.config import Config
from exceptions import BucketNotFoundError
from mypy_boto3_s3 import S3Client as S3ClientBoto3

logger = logging.getLogger(__name__)

CONFIG = Config(request_checksum_calculation="when_required", response_checksum_validation="when_required")


class S3Client:
    def __init__(self, s3_endpoint, access, secret):
        self._client: S3ClientBoto3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            region_name="us",
            config=CONFIG,
        )

    def upload_to_s3(self, response, bucket, object, chunk_size, calculate_checksum, progress_callback, total_size):
        md5_hash = hashlib.md5() if calculate_checksum else None
        downloaded_size = 0
        try:
            part_upload_init = self._client.create_multipart_upload(Bucket=bucket, Key=object)
            upload_id = part_upload_init["UploadId"]
            parts_list = []
            part_num = 1

            print("obj", object)
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
