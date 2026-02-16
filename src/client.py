import logging
from ftplib import FTP
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from auth import Auth
from downloader import get_downloader
from downloader.models import DownloadResult
from downloader.progress_logger import ProgressLogger
from exceptions import ValidationError
from requests import Session
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

        client = Client.ftp_login("anonymous", "user@email.com") # with ftp with email as password
        result = client.download(url)
    """

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        session: Optional[Session | FTP] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        if token:
            self._token = token
            self._session = self.create_session(token=token, timeout=timeout, max_retries=max_retries)
        else:
            self._session = session
        self._downloader = get_downloader(url=url, session=self._session)

        logger.info("Client initialized")

    @classmethod
    def from_credentials(
        cls, url: str, username: str, password: str, timeout: int = 30, max_retries: int = 3
    ) -> "Client":
        logger.info(f"Generating token for user: {username}")
        auth = Auth.from_credentials(username, password, timeout=timeout)
        session = cls.create_session(token=auth.token, timeout=timeout, max_retries=max_retries)
        return cls(url=url, session=session)

    @staticmethod
    def create_session(token, timeout, max_retries):
        auth = Auth(token=token)
        config = SessionConfig(timeout=timeout, max_retries=max_retries)
        session_manager = SessionManager(auth=auth, config=config)
        return session_manager.session

    @classmethod
    def ftp_login(cls, url, username, password):
        parsed = urlparse(url)
        logger.info(f"Connecting to server: {parsed.netloc}")
        ftp_session = FTP(parsed.netloc)
        ftp_session.login(username, password)
        ftp_session.voidcmd("TYPE I")
        return cls(url=url, session=ftp_session)

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
            progress_callback, close_progress = ProgressLogger.create_progress_bar()

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

    @staticmethod
    def validate_url(url: str) -> None:
        if not url:
            raise ValidationError("url cannot be empty")

        if not isinstance(url, str):
            raise ValidationError("url must be a string")

        parsed = urlparse(url)

        if not parsed.scheme:
            raise ValidationError("url must include scheme (http/https/ftp)")

        if parsed.scheme not in ("http", "https", "ftp"):
            raise ValidationError(f"unsupported url scheme: {parsed.scheme}")

        if not parsed.netloc:
            raise ValidationError("url must include host")

        return url

    @property
    def token(self) -> str:
        return self._token
