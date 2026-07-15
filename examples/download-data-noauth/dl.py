import logging
import os
import subprocess
import sys

# ------------------  input and output directory ------------------ #
pren = os.environ.get("HOMEDRIVE", "") if os.name == "nt" else "/"
data_output_path = os.path.join(pren, "data", "outputs")
os.makedirs(data_output_path, exist_ok=True)


# ------------------ log to output log file ------------------ #
LOG_FILE = os.path.join(data_output_path, "output.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

logger.info("Running within DAFNI — output path: %s", data_output_path)
logger.info("Python version: %s", sys.version)
logger.info("Output path : %s", data_output_path)
logger.info("Log file    : %s", LOG_FILE)


# -------- read values from environment variables ----------- #
CEDA_URL_DEFAULT: str = "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" 
ceda_url: str | None = os.getenv(key="CEDA_URL", default=CEDA_URL_DEFAULT)

# ------------------ Run downloader as CLI ------------------ #
cmd: list[str | None] = [
    "dataset-download-tool",
    "--no-auth",
    "--url",
    ceda_url,
    "--dest",  
    data_output_path, # must be /data/outputs for DAFNI
    "--log-file",
    LOG_FILE,
]

logger.info("Starting download — command: %s", " ".join(cmd))

try:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        args=cmd,
        check=True,
        capture_output=True,
        text=True,
    )
    logger.info("Download completed successfully.")
    if result.stdout:
        logger.info("Tool stdout:\n%s", result.stdout.strip())
    if result.stderr:
        logger.warning("Tool stderr:\n%s", result.stderr.strip())

except FileNotFoundError:
    logger.error("dataset-download-tool not found. Make sure it is installed and on your PATH.")
    sys.exit(0)

except subprocess.CalledProcessError as exc:
    logger.error("dataset-download-tool exited with code %d.", exc.returncode)
    if exc.stdout:
        logger.error("stdout:\n%s", exc.stdout.strip())
    if exc.stderr:
        logger.error("stderr:\n%s", exc.stderr.strip())
    sys.exit(exc.returncode)
