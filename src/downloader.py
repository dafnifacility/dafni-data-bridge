
class Downloader:
    def __init__(self, session, url: str):
        self.session = session
        self.url = url.rstrip("/")

    def download(self, url: str) -> bytes:
        response = self.session.get(url)

        if not response.ok:
            raise ValueError(
                f"Failed to download {url}: {response.status_code}"
            )

        return response.content