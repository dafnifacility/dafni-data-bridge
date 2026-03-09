import logging
from typing import Callable

from ceda_download_tool.downloader.models import ProgressCallback

logger = logging.getLogger(__name__)


class ProgressLogger:
    def create_progress_logger(log_interval_mb: float = 10.0) -> ProgressCallback:
        """Create a progress callback that logs download progress.

        Args:
            log_interval_mb: log progress every N megabytes.

        Returns:
            progress callback function.

        """
        last_logged_mb = [0.0]

        def log_progress(downloaded: int, total: int) -> None:
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024) if total else 0

            if downloaded_mb - last_logged_mb[0] >= log_interval_mb:
                if total_mb > 0:
                    percent = (downloaded / total) * 100
                    logger.info(f"progress: {downloaded_mb:.1f}/{total_mb:.1f} mb ({percent:.1f}%)")
                else:
                    logger.info(f"progress: {downloaded_mb:.1f} mb downloaded")

                last_logged_mb[0] = downloaded_mb

        return log_progress

    def create_progress_bar(desc: str = "downloading") -> tuple[ProgressCallback, Callable[[], None]]:
        """Create a simple console progress bar.

        Args:
            desc: description to show before progress bar.

        Returns:
            tuple of (progress_callback, close_function).

        """
        state = {"last_percent": -1}

        def show_progress(downloaded: int, total: int) -> None:
            if total <= 0:
                return

            percent = int((downloaded / total) * 100)

            if percent != state["last_percent"]:
                bar_length = 40
                filled = int(bar_length * downloaded / total)
                bar = "=" * filled + "-" * (bar_length - filled)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)

                print(f"\r{desc}: [{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} mb)", end="", flush=True)
                state["last_percent"] = percent

        def close() -> None:
            print()  # new line after progress bar

        return show_progress, close
