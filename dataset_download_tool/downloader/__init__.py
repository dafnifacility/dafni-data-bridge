import os
from ftplib import FTP
from typing import Optional

from paramiko import SSHClient
from requests import Session

from dataset_download_tool.downloader.services.ftp_service import FTPDownloader
from dataset_download_tool.downloader.services.http_gws import HTTPDownloaderGWS
from dataset_download_tool.downloader.services.http_service import HTTPDownloader
from dataset_download_tool.downloader.services.ssh_service import SSHDownloader

GWS_HOST = os.environ.get("GWS_BASE_URL", "https://gws-access")


def get_downloader(url: str, session: Optional[Session | FTP | SSHClient] = None):
    """Factory function to call appropriate downloader instance based on protocol

    Args:
        url: The target string starting with http(s):// or ftp://.
        session: A session object for the connection.

    """
    if url.startswith(GWS_HOST):
        return HTTPDownloaderGWS(session=session)
    elif url.startswith(("http://", "https://")):
        return HTTPDownloader(session=session)
    elif url.startswith("ftp://"):
        return FTPDownloader(session=session)
    else:
        return SSHDownloader(session=session)
