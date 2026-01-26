import logging
from pathlib import Path
from typing import Optional

from auth import Auth
from downloader import Downloader, DownloadResult, create_progress_bar
from session import SessionConfig, SessionManager

logger = logging.getLogger(__name__)


class Client:
    """
    high-level client for downloading data from ceda archives,
    provides simple interface combining authentication, session, downloads

    Example:
        client = Client(token="your_access_token")               # with existing token
        result = client.download(url, destination="./data/")

        client = Client.from_credentials("username", "password") # with credentials
        result = client.download(url)
    """

    def __init__(self, token: str, timeout: int = 30, max_retries: int = 3):
        self._auth = Auth(token=token)
        self._config = SessionConfig(timeout=timeout, max_retries=max_retries)
        self._session_manager = SessionManager(auth=self._auth, config=self._config)
        self._downloader = Downloader(session=self._session_manager.session)

        logger.info("Client initialized")

    @classmethod
    def from_credentials(cls, username: str, password: str, timeout: int = 30, max_retries: int = 3) -> "Client":
        logger.info(f"Generating token for user: {username}")
        auth = Auth.from_credentials(username, password, timeout=timeout)
        return cls(token=auth.token, timeout=timeout, max_retries=max_retries)

    def download(
        self,
        url: str,
        destination: Optional[str | Path] = None,
        show_progress: bool = True,
        calculate_checksum: bool = False,
    ) -> DownloadResult:
        """
        Args:
            url: url to download
            destination: target file path or directory
            show_progress: whether to show progress bar
            calculate_checksum: whether to calculate MD5 checksum

        Returns:
            DownloadResult
        """
        progress_callback = None
        close_progress = None

        if show_progress:
            progress_callback, close_progress = create_progress_bar()

        try:
            result = self._downloader.download(
                url=url,
                destination=destination,
                progress_callback=progress_callback,
                calculate_checksum=calculate_checksum,
            )
        finally:
            if close_progress:
                close_progress()

        return result

    def download_bytes(self, url: str) -> bytes:
        """
        download file content to memory

        Args:
            url: url to download

        Returns:
            file content as bytes
        """
        return self._downloader.download_bytes(url)

    @property
    def token(self) -> str:
        return self._auth.token
