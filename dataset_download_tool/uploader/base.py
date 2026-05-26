from abc import ABC, abstractmethod
from typing import Iterable, Optional, TYPE_CHECKING
from dataset_download_tool.downloader.models import ProgressCallback

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


