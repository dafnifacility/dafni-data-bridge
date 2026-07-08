import hashlib
import logging
import os
import uuid
from typing import Iterable, Optional, TYPE_CHECKING

from azure.storage.blob import BlobServiceClient, BlobBlock
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError, HttpResponseError


from dataset_download_tool.downloader.models import ProgressCallback
from dataset_download_tool.exceptions import AuthError, BucketNotFoundError, ValidationError
from dataset_download_tool.storage_selector.base import BaseUploader

logger = logging.getLogger(__name__)

ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_KEY=os.environ.get("AZURE_STORAGE_KEY")

class AzureBlobClient(BaseUploader):

    CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self, blob_url: str):
        if not ACCOUNT_NAME:
            raise ValidationError(
                "AZURE_STORAGE_ACCOUNT_NAME environment variable is not set"
            )
        try:
            account_url = f"{blob_url}/{ACCOUNT_NAME}"
            self._client = BlobServiceClient(
                account_url=account_url,
                credential=AZURE_STORAGE_KEY,
                connection_timeout=10,
                read_timeout=120,
                retry_total=5,
            )
            logger.info("Azure blob connection established!")
        except ValueError as e:
            logger.error(f"Cannot Access Azure URL: {e}")
            raise ValidationError(
                f"Invalid Azure endpoint URL: {blob_url}. "
                f"Ensure it follows the format: https://<container>.blob.core.windows.net/dir"
            )

    def upload(
        self,
        chunk_iter: Iterable[bytes],
        bucket: str,
        key: str,
        total_size: float = 0,
        calculate_checksum: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict:
        
        md5_hash = hashlib.md5() if calculate_checksum else None
        blob_client = self._client.get_blob_client(container=bucket, blob=key)
        block_list = []
        upload_size = 0
        buffer = bytearray()

        try:
            for chunk in chunk_iter:
                buffer.extend(chunk)
                upload_size += len(chunk)

                if md5_hash:
                    md5_hash.update(chunk)

                if len(buffer) >= self.CHUNK_SIZE:
                    block_id = self._stage_block(blob_client, bytes(buffer))
                    block_list.append(BlobBlock(block_id=block_id))
                    logger.debug(f"Staged block {len(block_list)}, size: {len(buffer)} bytes")
                    buffer.clear()

                if progress_callback:
                    progress_callback(upload_size, total_size)

            if buffer:
                block_id = self._stage_block(blob_client, bytes(buffer))
                block_list.append(BlobBlock(block_id=block_id))
                logger.debug(f"Staged final block {len(block_list)}, size: {len(buffer)} bytes")

            blob_client.commit_block_list(block_list)
            destination = blob_client.url
            checksum = md5_hash.hexdigest() if md5_hash else None
            logger.info(f"Successfully completed block upload to {destination}")

            return {
                "destination": destination,
                "size_bytes": upload_size,
                "checksum": checksum,
            }

        except ResourceNotFoundError:
            logger.error(f"Container not found: {bucket}")
            self._abort_block_upload(blob_client, key)
            raise BucketNotFoundError(
                f"Failed to upload to container: {bucket}. "
                f"Please ensure the container exists at: {self._client.url}"
            )
        except ClientAuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            self._abort_block_upload(blob_client, key)
            raise AuthError(f"Cannot access {bucket}: {e}")
        except HttpResponseError as e:
            logger.error(f"HTTP response error: {e}")
            self._abort_block_upload(blob_client, key)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            self._abort_block_upload(blob_client, key)
            raise


    def _stage_block(self, blob_client, data: bytes) -> str:
        """Stage a single block and return its block ID."""
        block_id = uuid.uuid4().hex
        blob_client.stage_block(block_id=block_id, data=data)
        return block_id
    
    def _abort_block_upload(self, blob_client, key: str) -> None:
        """
        Clean up a failed upload by deleting the blob if it exists.
        Note: uncommitted blocks are automatically purged by Azure after 7 days.
        """
        try:
            logger.warning(f"Aborting block upload for blob: {key}")
            blob_client.delete_blob()
            logger.info(f"Successfully deleted blob {key}")
        except ResourceNotFoundError:
            pass 
        except Exception as e:
            logger.error(f"Failed to abort block upload for {key}: {e}")