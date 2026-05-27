import logging

from dataset_download_tool.storage_selector.s3_upload import S3Client
from dataset_download_tool.storage_selector.azure_upload import AzureBlobClient
from dataset_download_tool.exceptions import ValidationError

logger = logging.getLogger(__name__)

def get_uploader(storage: str, endpoint_url: str):

    if storage==1:
        return S3Client(endpoint_url)
    elif storage==2:
        return AzureBlobClient(endpoint_url)
