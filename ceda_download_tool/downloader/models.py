from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class DownloadResult:
    """Represents the metadata of downloaded files.

    Attributes:
        url: The source URL or a list of URLs from which data was retrieved.
        destination: The local Path or list of Paths where files were saved.
        size_bytes: The total size of the downloaded data in bytes.
        checksum: An optional hash (e.g., MD5, SHA-256) for file verification

    """

    url: str | list[str]
    destination: Path | list[Path]
    size_bytes: int
    checksum: Optional[str] = None

    @property
    def size_mb(self) -> float:
        """The total download size converted to Megabytes (MiB)."""
        return self.size_bytes / (1024 * 1024)


ProgressCallback = Callable[[int, int], None]
"""Callback receiving (bytes_received, total_bytes)."""
