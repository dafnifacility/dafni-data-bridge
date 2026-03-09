import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str | Path] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
) -> logging.Logger:
    """Args:
        level: logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: optional path to log file. If provided, logs to both console and file
        log_format: custom log format string
        date_format: custom date format string

    Returns:
        configured root logger

    Example:
        setup_logging()         # basic console logging
        setup_logging(          # Debug level with file output
            level=logging.DEBUG,
            log_file="downloads.log"
        )

    """
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    formatter = logging.Formatter(log_format, datefmt=date_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        root_logger.info(f"logging to file: {log_path.absolute()}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
