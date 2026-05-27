import paramiko

from dataset_download_tool.downloader.base import BaseDownloader
from dataset_download_tool.downloader.download_utils import extract_filename
from dataset_download_tool.downloader.models import DownloadResult
from dataset_download_tool.storage_selector.selector_utils import append_bucket_url


class SSHDownloader(BaseDownloader):
    """
    SSH implementation of file downloader

    This class inherits from BaseDownloader and handles stream logic as well as checking contents

    Args:
        session: A paramiko.client.SSHClient object
    """

    def __init__(self, session):
        super().__init__(session)
        self._sftp = self._session.open_sftp()

    def _is_directory(self, path):
        """Check if path points to a directory"""
        try:
            self._sftp.chdir(path)
            return True
        except paramiko.SFTPError:
            return False

    def _directory_contents(self, path: str):
        """gets directory files"""
        items_path = [f"{path}{file}" if path.endswith("/") else f"{path}/{file}" for file in self._sftp.listdir(path)]

        return items_path

    def _recursive_download(self, path, destination, calculate_checksum, progress_callback) -> list[DownloadResult]:
        """Download all files in a directory"""

        file_list = []
        contents = self._directory_contents(path)
        if isinstance(destination, dict):
            destination = append_bucket_url(destination)
        for item_path in contents:
            filename = extract_filename(item_path)
            dest_path = f"{destination}/{filename}"
            result = self.download(
                url=item_path,
                destination=dest_path,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
            )
            file_list.append(result)
        return file_list

    def _stream(self, path):
        """Create data stream to call files in chunks.

        Returns:
            generator: A generator that yields chunks of data
            int: total numver of bytes

        """

        file = self._sftp.file(path, mode="rb")
        total_size = file.stat().st_size

        def generator():
            with self._sftp.open(path, "rb") as remote_file:
                remote_file.prefetch()
                while True:
                    chunk = remote_file.read(self._chunk_size)
                    if not chunk:
                        break
                    yield chunk

        return generator(), total_size
