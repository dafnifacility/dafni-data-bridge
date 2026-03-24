import logging
import os
import subprocess
import sys
 
gPATHI = ""
gPATHO = ""
 
isDAFNI = os.environ.get("ISDAFNI")
 
if isDAFNI == "True":
    pren = os.environ.get("HOMEDRIVE", "") if os.name == "nt" else "/"
    gPATHI = os.path.join(pren, "data", "inputs")
    gPATHO = os.path.join(pren, "data", "outputs")
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gPATHI = os.path.join(script_dir, "data", "inputs")
    gPATHO = os.path.join(script_dir, "data", "outputs")
 
os.makedirs(gPATHO, exist_ok=True)
 
LOG_FILE = os.path.join(gPATHO, "download.log")
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
 
logger.info("ISDAFNI environment variable = %s (%s)", isDAFNI, type(isDAFNI).__name__)
 
if isDAFNI == "True":
    logger.info("Running within DAFNI — output path: %s", gPATHO)
else:
    logger.info("Not running within DAFNI — using local paths")
 
logger.info("Python version: %s", sys.version)
logger.info("Input  path : %s", gPATHI)
logger.info("Output path : %s", gPATHO)
logger.info("Log file    : %s", LOG_FILE)
 
CONFIG_FILENAME = "download_args.json"
config_path = os.path.join(gPATHI, CONFIG_FILENAME)
 
if not os.path.isfile(config_path):
    logger.error("Config file not found: %s", config_path)
    sys.exit(0)
 
logger.info("Using config file: %s", config_path)
 
cmd = [
    "dataset-download-tool",
    "--config",
    config_path,
    "--dest",
    gPATHO,
    "--checksum",
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
    logger.error("ceda-download-tool not found. " "Make sure it is installed and on your PATH.")
    sys.exit(0)
 
except subprocess.CalledProcessError as exc:
    logger.error("ceda-download-tool exited with code %d.", exc.returncode)
    if exc.stdout:
        logger.error("stdout:\n%s", exc.stdout.strip())
    if exc.stderr:
        logger.error("stderr:\n%s", exc.stderr.strip())
    sys.exit(exc.returncode)