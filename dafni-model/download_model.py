import logging
import os
import subprocess
import sys
 
pren = os.environ.get("HOMEDRIVE", "") if os.name == "nt" else "/"
inputs_path = os.path.join(pren, "data", "inputs")
outputs_path = os.path.join(pren, "data", "outputs")
 
os.makedirs(outputs_path, exist_ok=True)
 
LOG_FILE = os.path.join(outputs_path, "download.log")
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

logger.info("Running within DAFNI — output path: %s", outputs_path)

logger.info("Python version: %s", sys.version)
logger.info("Input  path : %s", inputs_path)
logger.info("Output path : %s", outputs_path)
logger.info("Log file    : %s", LOG_FILE)
 
CONFIG_FILENAME = "download_args.json"
config_path = os.path.join(inputs_path, CONFIG_FILENAME)
 
if not os.path.isfile(config_path):
    logger.error("Config file not found: %s", config_path)
    sys.exit(0)
 
logger.info("Using config file: %s", config_path)

# Hard code output path, so user doesn't overwrite it
cmd = [
    "dataset-download-tool",
    "--config",
    config_path,
    "--dest",
    outputs_path,
    "--log-file",
    LOG_FILE,
]
 
logger.info("Starting download — command: %s", " ".join(cmd))
 
try:
    result = subprocess.run(
        cmd,
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
    logger.error("dataset-download-tool not found. " "Make sure it is installed and on your PATH.")
    sys.exit(0)
 
except subprocess.CalledProcessError as exc:
    logger.error("dataset-download-tool exited with code %d.", exc.returncode)
    if exc.stdout:
        logger.error("stdout:\n%s", exc.stdout.strip())
    if exc.stderr:
        logger.error("stderr:\n%s", exc.stderr.strip())
    sys.exit(exc.returncode)