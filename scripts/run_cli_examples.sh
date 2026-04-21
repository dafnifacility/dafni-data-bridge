#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# run_cli_examples.sh
#
# Runs all `dataset-download-tool` CLI commands documented in
# docs/user-guide/cli-reference.md sequentially.
#
# Required environment variables (set these before running):
#   CEDA_USERNAME      CEDA archive username
#   CEDA_PASSWORD      CEDA archive password
#   CEDA_TOKEN         CEDA access token
#   JASMIN_USERNAME    JASMIN GWS username
#   SSH_KEY            Path to SSH private key (no default - must be set)
#   ACCESS_KEY         S3 access key (for S3 destination examples)
#   SECRET_KEY         S3 secret key (for S3 destination examples)
#   S3_MINIO_DEST      MinIO S3 destination (e.g. http://test.localhost:9000/data/)
#   S3_STFC_DEST       STFC Echo S3 destination (e.g. https://ddttest.s3.echo.stfc.ac.uk/key)
#
# Optional:
#   FTP_EMAIL          Email to use as anonymous FTP password
#                      (default: anonymous@example.com)
#   DEST               Destination directory for downloads (default: ./data/)
#   CONFIG_FILE        JSON config file path (default: config.json)
#                      If explicitly set to a non-default value, file must exist
#   SLEEP_BETWEEN      Seconds to sleep between commands (default: 2)
#
# Usage:
#   export CEDA_USERNAME=... CEDA_PASSWORD=... CEDA_TOKEN=... JASMIN_USERNAME=...
#   export SSH_KEY=/path/to/your/private/key
#   export ACCESS_KEY=... SECRET_KEY=...
#   export S3_MINIO_DEST=http://test.localhost:9000/data/
#   export S3_STFC_DEST=https://ddttest.s3.echo.stfc.ac.uk/dataset
#   ./scripts/run_cli_examples.sh
# ------------------------------------------------------------------------------

set -u  # error on unset variables
# Note: we do NOT use `set -e` because we want all examples to be attempted
# even if one fails. Each command's exit code is reported at the end.

# ---- Defaults ---------------------------------------------------------------
SSH_KEY="${SSH_KEY:-}"  # No default - must be explicitly provided
FTP_EMAIL="${FTP_EMAIL:-anonymous@example.com}"
DEST="${DEST:-./data/}"
CONFIG_FILE="${CONFIG_FILE:-config.json}"
SLEEP_BETWEEN="${SLEEP_BETWEEN:-3}"

# ---- Required variable check -----------------------------------------------
REQUIRED_VARS=(CEDA_USERNAME CEDA_PASSWORD CEDA_TOKEN JASMIN_USERNAME ACCESS_KEY SECRET_KEY S3_MINIO_DEST S3_STFC_DEST SSH_KEY)
missing=0
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: required environment variable '$var' is not set" >&2
    missing=1
  fi
done
if [[ $missing -ne 0 ]]; then
  echo "Set the required environment variables and re-run." >&2
  exit 1
fi

# ---- Config file check -----------------------------------------------------
# If CONFIG_FILE is explicitly set (not default) or if default exists, validate it
if [[ -n "${CONFIG_FILE}" && "${CONFIG_FILE}" != "config.json" ]]; then
  # User explicitly set CONFIG_FILE, so it must exist
  if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "ERROR: CONFIG_FILE is set to '$CONFIG_FILE' but file does not exist" >&2
    exit 1
  fi
fi

mkdir -p "$DEST"

# ---- Helper -----------------------------------------------------------------
# Redact values that follow credential flags so they never print to the console.
mask_command() {
  local -a out=()
  local mask_next=0
  local arg
  for arg in "$@"; do
    if [[ $mask_next -eq 1 ]]; then
      out+=("***")
      mask_next=0
      continue
    fi
    case "$arg" in
      --token|-t|--password|-p|--username|-u)
        out+=("$arg")
        mask_next=1
        ;;
      *)
        out+=("$arg")
        ;;
    esac
  done
  printf '%s ' "${out[@]}"
}

declare -a RESULTS
step=0

# Inspect a command's arguments and report which login method it uses.
# Prints one of: none, token, user/pass, ssh-key, config, unknown
detect_auth() {
  local has_token=0 has_user=0 has_pass=0 has_key=0 has_noauth=0 has_config=0
  local arg
  for arg in "$@"; do
    case "$arg" in
      --token|-t)           has_token=1 ;;
      --username|-u)        has_user=1 ;;
      --password|-p)        has_pass=1 ;;
      --key-filename)       has_key=1 ;;
      --no-auth)            has_noauth=1 ;;
      --config)             has_config=1 ;;
    esac
  done
  if   [[ $has_noauth -eq 1 ]]; then echo "none"
  elif [[ $has_token  -eq 1 ]]; then echo "token"
  elif [[ $has_key    -eq 1 ]]; then echo "ssh-key"
  elif [[ $has_user   -eq 1 && $has_pass -eq 1 ]]; then echo "user/pass"
  elif [[ $has_config -eq 1 ]]; then echo "config"
  else echo "unknown"
  fi
}

# Inspect a command's arguments and report the source transport.
# Prints one of: http, https, ftp, ftps, ssh, config, unknown
detect_source() {
  local arg next_is_url=0 url=""
  for arg in "$@"; do
    if [[ $next_is_url -eq 1 ]]; then
      url="$arg"
      next_is_url=0
      continue
    fi
    case "$arg" in
      --ssh)     echo "ssh"; return ;;
      --config)  echo "config"; return ;;
      --url)     next_is_url=1 ;;
    esac
  done
  url="${url%% | *}"
  case "$url" in
    https://*) echo "https" ;;
    http://*)  echo "http"  ;;
    ftps://*)  echo "ftps"  ;;
    ftp://*)   echo "ftp"   ;;
    "")        echo "unknown" ;;
    *)         echo "unknown" ;;
  esac
}

# Inspect a command's arguments and report the destination type.
# Prints one of: s3, local, config, unknown
detect_dest() {
  local arg next_is_dest=0 dest="" has_config=0
  for arg in "$@"; do
    if [[ $next_is_dest -eq 1 ]]; then
      dest="$arg"
      next_is_dest=0
      continue
    fi
    case "$arg" in
      --dest)   next_is_dest=1 ;;
      --config) has_config=1 ;;
    esac
  done
  if [[ -z "$dest" && $has_config -eq 1 ]]; then
    echo "config"; return
  fi
  case "$dest" in
    "")                              echo "unknown" ;;
    http://*|https://*|s3://*)       echo "s3" ;;
    *)                               echo "local" ;;
  esac
}

run_step() {
  local name="$1"; shift
  step=$((step + 1))
  local auth src dst
  auth="$(detect_auth "$@")"
  src="$(detect_source "$@")"
  dst="$(detect_dest "$@")"
  echo
  echo "=============================================================="
  echo "➡️  [$step] $name  (auth: $auth, $src -> $dst)"
  echo "--------------------------------------------------------------"
  echo "🖥️  $(mask_command "$@")"
  echo "--------------------------------------------------------------"
  "$@"
  local rc=$?
  RESULTS+=("$step|$rc|$auth|$src|$dst|$name")
  echo "[$step] exit code: $rc"
  if [[ "$SLEEP_BETWEEN" != "0" ]]; then
    echo "[$step] sleeping ${SLEEP_BETWEEN}s before next command..."
    sleep "$SLEEP_BETWEEN"
  fi
}

# =============================================================================
# Logging and Debugging
# =============================================================================

run_step "Debug logging" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    --dest "$DEST" \
    --debug

run_step "Log file" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    --dest "$DEST" \
    --log-file ./download.log

run_step "Debug + log file" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    --dest "$DEST" \
    --debug --log-file ./download.log

# =============================================================================
# No Authentication
# =============================================================================

run_step "No auth download" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt" \
    --dest "$DEST"

# =============================================================================
# Username / Password Authentication
# =============================================================================

run_step "Username/password (env vars)" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    --dest "$DEST"

# =============================================================================
# Token Authentication
# =============================================================================

run_step "Token auth" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    --dest "$DEST"

# =============================================================================
# SSH Key Authentication (auth section)
# =============================================================================

run_step "SSH auth: single file with checksum" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/1GB.zip \
    --key-filename "$SSH_KEY" \
    --dest "$DEST" --checksum

run_step "SSH auth: entire directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

# =============================================================================
# Configuration File
# =============================================================================

if [[ ! -f "$CONFIG_FILE" ]]; then
  if [[ -f config.example.json ]]; then
    cp config.example.json "$CONFIG_FILE"
  else
    echo "NOTE: no $CONFIG_FILE and no config.example.json — skipping config examples"
  fi
fi

if [[ -f "$CONFIG_FILE" ]]; then
  run_step "Config file" \
    dataset-download-tool --config "$CONFIG_FILE"

  run_step "Config file with CLI override (--dest)" \
    dataset-download-tool --config "$CONFIG_FILE" --dest /tmp/
fi

# =============================================================================
# Download Options: Single URLs
# =============================================================================

run_step "Single URL" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz" \
    --dest "$DEST"

# =============================================================================
# Download Options: Multiple URLs
# =============================================================================

run_step "Multiple URLs (pipe-separated)" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz" \
    --dest "$DEST"

# =============================================================================
# Directory Downloads (HTTP)
# =============================================================================

run_step "HTTP directory download" \
  dataset-download-tool --no-auth \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    --dest "$DEST"

# =============================================================================
# GWS HTTP Downloads
# =============================================================================

run_step "GWS HTTP: single file" \
  dataset-download-tool --no-auth \
    --url "https://gws-access.jasmin.ac.uk/public/perf_testing/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc" \
    --dest "$DEST" --checksum

run_step "GWS HTTP: multiple files" \
  dataset-download-tool --no-auth \
    --url "https://gws-access.jasmin.ac.uk/public/perf_testing/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc | https://gws-access.jasmin.ac.uk/public/perf_testing/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc" \
    --dest "$DEST" --checksum

run_step "GWS HTTP: entire directory" \
  dataset-download-tool --no-auth \
    --url "https://gws-access.jasmin.ac.uk/public/perf_testing/testdir/" \
    --dest "$DEST" --checksum

# =============================================================================
# FTP Downloads
# =============================================================================

run_step "FTP: single file" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    --dest "$DEST"

run_step "FTP: multiple files" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    --dest "$DEST"

run_step "FTP: entire directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
    --dest "$DEST"

# =============================================================================
# SSH Downloads (downloads section)
# =============================================================================

run_step "SSH: single file" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    --key-filename "$SSH_KEY" \
    --dest "$DEST" --checksum

run_step "SSH: multiple files" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    --key-filename "$SSH_KEY" \
    --dest "$DEST" --checksum

run_step "SSH: entire directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --key-filename "$SSH_KEY" \
    --dest "$DEST" --checksum

# =============================================================================
# S3 Destination
# =============================================================================

run_step "S3 destination: MinIO (local)" \
  dataset-download-tool --no-auth \
    --url "https://gws-access.jasmin.ac.uk/public/perf_testing/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc" \
    --dest "$S3_MINIO_DEST" --checksum

run_step "S3 destination: STFC Echo" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/00README.txt" \
    --dest "$S3_STFC_DEST" --checksum

# =============================================================================
# Timeout and Retries
# =============================================================================

run_step "Timeout and retries" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    --dest "$DEST" --timeout 60 --retries 5

# =============================================================================
# Summary
# =============================================================================

echo
echo "=============================================================="
echo "Summary"
echo "=============================================================="
fail=0
for entry in "${RESULTS[@]}"; do
  IFS='|' read -r s rc auth src dst name <<< "$entry"
  if [[ "$rc" -eq 0 ]]; then
    status="OK  "
  else
    status="FAIL"
    fail=$((fail + 1))
  fi
  printf "[%2d] %s (rc=%s, auth=%-9s, %-7s -> %-7s)  %s\n" \
    "$s" "$status" "$rc" "$auth" "$src" "$dst" "$name"
done
echo "--------------------------------------------------------------"
echo "Total: ${#RESULTS[@]}  Failed: $fail"
exit $fail
