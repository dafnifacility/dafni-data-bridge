from ftplib import FTP
from typing import Optional

from requests import Session

from .ftp_service import FTPDownloader
from .http_service import HTTPDownloader


def get_downloader(url: str, session: Optional[Session | FTP] = None):
    """
    Factory function to call appropriate downloader instance based on protocol

    Args:
        url: The target string starting with http(s):// or ftp://.
        session: An optional pre-existing session object for the connection.
    """

    if url.startswith(("http://", "https://")):
        return HTTPDownloader(session=session)
    elif url.startswith("ftp://"):
        return FTPDownloader(session=session)
