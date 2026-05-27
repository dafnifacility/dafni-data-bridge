from urllib.parse import urljoin

from bs4 import BeautifulSoup

from dataset_download_tool.downloader.models import DownloadResult
from dataset_download_tool.downloader.services.http_service import HTTPDownloader
from dataset_download_tool.storage_selector.selector_utils import append_bucket_url


class HTTPDownloaderGWS(HTTPDownloader):
    """GWS specfic HTTP downloader for Jasmin

    Inherits from:
        HTTPDownloader
    """

    def _get_soup(self, url):
        """Gets html contents from link"""
        with self._session.get(url) as response:
            return BeautifulSoup(response.text, "html.parser")

    def _is_directory(self, url) -> bool:
        """Checks if it is a directory"""
        self._soup = self._get_soup(url)
        if self._soup.title and self._soup.title.string:
            return self._soup.title.string.startswith("Index of")
        return False

    def _directory_contents(self, url) -> dict:
        """Extracts all the files and objects from url"""
        contents = []
        for link in self._soup.find_all("a"):
            href = link.get("href")
            # skip any things that are not needed like order query
            if "Parent Directory" in link.text:
                continue
            if "?" in href:
                continue
            contents.append(href)

        return contents

    def _recursive_download(self, url, destination, calculate_checksum, progress_callback, storage) -> list[DownloadResult]:
        """Downloads all files in a directory"""
        file_list = []
        contents = self._directory_contents(url)
        if isinstance(destination, dict):
            destination = append_bucket_url(destination)
        for file in contents:
            item_url = urljoin(url, file)
            dest_path = f"{destination}/{file}"
            result = self.download(
                url=item_url,
                destination=dest_path,
                calculate_checksum=calculate_checksum,
                progress_callback=progress_callback,
                storage=storage
            )
            file_list.append(result)

        return file_list
