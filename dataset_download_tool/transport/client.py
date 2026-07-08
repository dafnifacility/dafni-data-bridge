import logging
from ftplib import FTP, error_perm
from pathlib import Path
from socket import gaierror
from typing import Optional
from urllib.parse import urlparse

from paramiko import AuthenticationException, AutoAddPolicy, SSHClient
from requests import Session

from dataset_download_tool.downloader import get_downloader
from dataset_download_tool.downloader.models import DownloadResult
from dataset_download_tool.downloader.progress_logger import ProgressLogger
from dataset_download_tool.exceptions import AuthError, ValidationError
from dataset_download_tool.transport.auth import Auth
from dataset_download_tool.transport.session import create_session

logger = logging.getLogger(__name__)


class Client:
    """high-level client for downloading data from ceda archives,
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
        if token or token == "no_auth":
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
        session = create_session(auth=auth, timeout=timeout, max_retries=max_retries)
        return cls(url=url, session=session)

    @staticmethod
    def create_session(token, timeout, max_retries):
        auth = Auth(token=token) if token != "no_auth" else None
        return create_session(auth=auth, timeout=timeout, max_retries=max_retries)

    @classmethod
    def ssh_client(cls, url, hostname, username, key_filename) -> "Client":
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        try:
            ssh.connect(hostname=hostname, username=username, key_filename=key_filename)
            return cls(url=url, session=ssh)
        except AuthenticationException as e:
            logger.error(f"Could not access {hostname}")
            raise AuthError(f"Please check username or key: {e}")
        except gaierror as e:
            logger.error(e)
            raise ValidationError(f"Could not access {hostname}, please enter valid host")
        except FileNotFoundError as e:
            logger.error(e)
            raise ValidationError("Please insert valid path for key")

    @classmethod
    def ftp_login(cls, url, username, password):
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 21
        logger.info(f"Connecting to server: {parsed.netloc}")
        try:
            ftp_session = FTP()
            ftp_session.connect(host, port)
            ftp_session.login(username, password)
            ftp_session.voidcmd("TYPE I")
            return cls(url=url, session=ftp_session)
        except gaierror as e:
            logger.error(f"Could not access {url}")
            raise ValidationError(f"Invalid URL: {url}: {e}")
        except error_perm as e:
            logger.error("Access error! NOTE: use anonymous as username and email as password for CEDA FTP")
            raise AuthError(f"Could not access {url}: {e}")

    def download(
        self,
        url: str,
        destination: Optional[str | Path] = None,
        show_progress: bool = True,
        calculate_checksum: bool = False,
        storage: str = "local"
    ) -> DownloadResult:
        """Args:
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
                storage=storage,
            )
        finally:
            if close_progress:
                close_progress()

        return result

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
