import logging
import pathlib as Path
from urllib.parse import urlparse

from abc import ABC, abstractmethod
from typing import Iterable, Optional, TYPE_CHECKING

from dataset_download_tool.downloader.models import ProgressCallback
from dataset_download_tool.downloader.download_utils import extract_filename
from dataset_download_tool.exceptions import ValidationError

logger = logging.getLogger(__name__)

class BaseUploader(ABC):

    @abstractmethod
    def upload(
        self,
        chunk_iter: Iterable[bytes],
        bucket: str,
        key: str,
        total_size: float = 0,
        calculate_checksum: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict:
        pass
