import hashlib
import logging
import os
from typing import Iterable, Optional, TYPE_CHECKING

from azure.storage.blob import BlobServiceClient

from dataset_download_tool.downloader.models import ProgressCallback
from dataset_download_tool.exceptions import AuthError, BucketNotFoundError

logger = logging.getLogger(__name__)

AZURE_STOAGE_KEY=os.environ.get("AZURE_STORAGE_KEY")

# class AzureClient:

#     def __init__(self, blob_url):

#         self._client