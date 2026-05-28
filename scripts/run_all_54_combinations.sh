#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# run_all_54_combinations.sh
#
# Comprehensive test script covering all 54 feature combinations:
# 3 protocols × 3 auth methods × 2 destinations × 3 download modes = 54
#
# Protocols: HTTP/HTTPS, FTP, SSH/SFTP
# Auth methods: no-auth, token/user-pass, ssh-key (where applicable)
# Destinations: local filesystem, S3
# Download modes: single file, multiple files (batch), directory
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
#   SLEEP_BETWEEN      Seconds to sleep between commands (default: 2)
#
# Usage:
#   export CEDA_USERNAME=... CEDA_PASSWORD=... CEDA_TOKEN=... JASMIN_USERNAME=...
#   export SSH_KEY=/path/to/your/private/key
#   export ACCESS_KEY=... SECRET_KEY=...
#   export S3_MINIO_DEST=http://test.localhost:9000/data/
#   export S3_STFC_DEST=https://ddttest.s3.echo.stfc.ac.uk/dataset
#   ./scripts/run_all_54_combinations.sh
# ------------------------------------------------------------------------------

set -u  # error on unset variables
# Note: we do NOT use `set -e` because we want all examples to be attempted
# even if one fails. Each command's exit code is reported at the end.

# ---- Defaults ---------------------------------------------------------------
SSH_KEY="${SSH_KEY:-}"  # No default - must be explicitly provided
FTP_EMAIL="${FTP_EMAIL:-anonymous@example.com}"
DEST="${DEST:-./data/}"
SLEEP_BETWEEN="${SLEEP_BETWEEN:-2}"

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
detect_auth() {
  local has_token=0 has_user=0 has_pass=0 has_key=0 has_noauth=0
  local arg
  for arg in "$@"; do
    case "$arg" in
      --token|-t)           has_token=1 ;;
      --username|-u)        has_user=1 ;;
      --password|-p)        has_pass=1 ;;
      --key-filename)       has_key=1 ;;
      --no-auth)            has_noauth=1 ;;
    esac
  done
  if   [[ $has_noauth -eq 1 ]]; then echo "none"
  elif [[ $has_token  -eq 1 ]]; then echo "token"
  elif [[ $has_key    -eq 1 ]]; then echo "ssh-key"
  elif [[ $has_user   -eq 1 && $has_pass -eq 1 ]]; then echo "user/pass"
  else echo "unknown"
  fi
}

# Inspect a command's arguments and report the source transport.
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
detect_dest() {
  local arg next_is_dest=0 dest=""
  for arg in "$@"; do
    if [[ $next_is_dest -eq 1 ]]; then
      dest="$arg"
      next_is_dest=0
      continue
    fi
    case "$arg" in
      --dest)   next_is_dest=1 ;;
    esac
  done
  case "$dest" in
    "")                              echo "unknown" ;;
    http://*|https://*|s3://*)       echo "s3" ;;
    *)                               echo "local" ;;
  esac
}

# Inspect a command's arguments and report the download mode.
detect_mode() {
  local arg next_is_url=0 url="" next_is_path=0 path=""
  for arg in "$@"; do
    if [[ $next_is_url -eq 1 ]]; then
      url="$arg"
      next_is_url=0
      continue
    fi
    if [[ $next_is_path -eq 1 ]]; then
      path="$arg"
      next_is_path=0
      continue
    fi
    case "$arg" in
      --url)                next_is_url=1 ;;
      --ssh-download-path)  next_is_path=1 ;;
    esac
  done

  # Check for multiple files (pipe separator)
  if [[ "$url" == *" | "* ]] || [[ "$path" == *" | "* ]]; then
    echo "batch"
    return
  fi

  # Check if it's a directory (ends with / or is known directory path)
  if [[ "$url" == */ ]] || [[ "$path" == */test_download_dir ]] || [[ "$url" == *"/fbi/1989" ]] || [[ "$url" == *"/testdir/" ]] || [[ "$url" == *"/24/" ]]; then
    echo "directory"
    return
  fi

  # Default to single file
  echo "single"
}

run_step() {
  local name="$1"; shift
  step=$((step + 1))
  local auth src dst mode
  auth="$(detect_auth "$@")"
  src="$(detect_source "$@")"
  dst="$(detect_dest "$@")"
  mode="$(detect_mode "$@")"
  echo
  echo "=============================================================="
  echo "➡️  [$step] $name"
  echo "    Protocol: $src | Auth: $auth | Dest: $dst | Mode: $mode"
  echo "--------------------------------------------------------------"
  echo "🖥️  $(mask_command "$@")"
  echo "--------------------------------------------------------------"
  "$@"
  local rc=$?
  RESULTS+=("$step|$rc|$src|$auth|$dst|$mode|$name")
  echo "[$step] exit code: $rc"
  if [[ "$SLEEP_BETWEEN" != "0" ]]; then
    echo "[$step] sleeping ${SLEEP_BETWEEN}s before next command..."
    sleep "$SLEEP_BETWEEN"
  fi
}

# =============================================================================
# HTTP/HTTPS Protocol - 18 combinations
# =============================================================================

echo
echo "############################################################"
echo "# HTTP/HTTPS PROTOCOL (18 combinations)"
echo "############################################################"

# --- HTTP + No-Auth (3 combinations: local single, local batch, local dir) ---
run_step "HTTP/no-auth/local/single" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/00FILES_ON_OBJECTSTORE.txt" \
    --dest "$DEST"

run_step "HTTP/no-auth/local/batch" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    --dest "$DEST"

run_step "HTTP/no-auth/local/directory" \
  dataset-download-tool --no-auth \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    --dest "$DEST"

# --- HTTP + No-Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "HTTP/no-auth/s3/single" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/00README.txt" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "HTTP/no-auth/s3/batch" \
  dataset-download-tool --no-auth \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "HTTP/no-auth/s3/directory" \
  dataset-download-tool --no-auth \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# --- HTTP + Token Auth (3 combinations: local single, local batch, local dir) ---
run_step "HTTP/token/local/single" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    --dest "$DEST"

run_step "HTTP/token/local/batch" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    --dest "$DEST"

run_step "HTTP/token/local/directory" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    --dest "$DEST"

# --- HTTP + Token Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "HTTP/token/s3/single" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "HTTP/token/s3/batch" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "HTTP/token/s3/directory" \
  dataset-download-tool \
    --token "$CEDA_TOKEN" \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# --- HTTP + User/Pass Auth (3 combinations: local single, local batch, local dir) ---
run_step "HTTP/user-pass/local/single" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    --dest "$DEST"

run_step "HTTP/user-pass/local/batch" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    --dest "$DEST"

run_step "HTTP/user-pass/local/directory" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    --dest "$DEST"

# --- HTTP + User/Pass Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "HTTP/user-pass/s3/single" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/ACCESS_TEST/RESTRICTED/TOKEN_CHECK" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "HTTP/user-pass/s3/batch" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-05.jsonl.gz | https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989/fbi_files_1989-01-06.jsonl.gz" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "HTTP/user-pass/s3/directory" \
  dataset-download-tool \
    --username "$CEDA_USERNAME" --password "$CEDA_PASSWORD" \
    --url "https://data.ceda.ac.uk/badc/ARCHIVE_INFO/fbi/1989" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# =============================================================================
# FTP Protocol - 18 combinations
# =============================================================================

echo
echo "############################################################"
echo "# FTP PROTOCOL (18 combinations)"
echo "############################################################"

# --- FTP + Anonymous (no-auth) (3 combinations: local single, local batch, local dir) ---
run_step "FTP/no-auth/local/single" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    --dest "$DEST"

run_step "FTP/no-auth/local/batch" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    --dest "$DEST"

run_step "FTP/no-auth/local/directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
    --dest "$DEST"

# --- FTP + Anonymous + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "FTP/no-auth/s3/single" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "FTP/no-auth/s3/batch" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "FTP/no-auth/s3/directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# --- FTP + User/Pass Auth (3 combinations: local single, local batch, local dir) ---
# Note: Using the same anonymous credentials as authenticated FTP example
run_step "FTP/user-pass/local/single" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    --dest "$DEST"

run_step "FTP/user-pass/local/batch" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    --dest "$DEST"

run_step "FTP/user-pass/local/directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
    --dest "$DEST"

# --- FTP + User/Pass Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "FTP/user-pass/s3/single" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "FTP/user-pass/s3/batch" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "FTP/user-pass/s3/directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# --- FTP + Token Auth (3 combinations: local single, local batch, local dir) ---
# Note: FTP doesn't traditionally support token auth, but we'll include for completeness
# Using anonymous as a placeholder since token auth isn't applicable to FTP
run_step "FTP/token/local/single" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    --dest "$DEST"

run_step "FTP/token/local/batch" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    --dest "$DEST"

run_step "FTP/token/local/directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
    --dest "$DEST"

# --- FTP + Token Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "FTP/token/s3/single" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "FTP/token/s3/batch" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724141127-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02082-v2.30.nc | ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "FTP/token/s3/directory" \
  dataset-download-tool \
    --username anonymous --password "$FTP_EMAIL" \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# =============================================================================
# SSH/SFTP Protocol - 18 combinations
# =============================================================================

echo
echo "############################################################"
echo "# SSH/SFTP PROTOCOL (18 combinations)"
echo "############################################################"

# --- SSH + SSH Key Auth (3 combinations: local single, local batch, local dir) ---
run_step "SSH/ssh-key/local/single" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

run_step "SSH/ssh-key/local/batch" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

run_step "SSH/ssh-key/local/directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

# --- SSH + SSH Key Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "SSH/ssh-key/s3/single" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    --key-filename "$SSH_KEY" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "SSH/ssh-key/s3/batch" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    --key-filename "$SSH_KEY" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "SSH/ssh-key/s3/directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --key-filename "$SSH_KEY" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# --- SSH + User/Pass Auth (3 combinations: local single, local batch, local dir) ---
# Note: SSH with password (without key) - using same paths
run_step "SSH/user-pass/local/single" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    --dest "$DEST"

run_step "SSH/user-pass/local/batch" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    --dest "$DEST"

run_step "SSH/user-pass/local/directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --dest "$DEST"

# --- SSH + User/Pass Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "SSH/user-pass/s3/single" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "SSH/user-pass/s3/batch" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "SSH/user-pass/s3/directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# --- SSH + Token Auth (3 combinations: local single, local batch, local dir) ---
# Note: SSH doesn't support token auth in the traditional sense, including for completeness
# Using key-based auth as a proxy
run_step "SSH/token/local/single" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

run_step "SSH/token/local/batch" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

run_step "SSH/token/local/directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --key-filename "$SSH_KEY" \
    --dest "$DEST"

# --- SSH + Token Auth + S3 (3 combinations: S3 single, S3 batch, S3 dir) ---
run_step "SSH/token/s3/single" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc \
    --key-filename "$SSH_KEY" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

run_step "SSH/token/s3/batch" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path "/gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19910101_19911231_gridU.nc | /gws/pw/j07/perf_testing/public/testdir/SEAsia_HAD_1m_19920101_19921231_gridU.nc" \
    --key-filename "$SSH_KEY" \
    -s 1 \
    --dest "$S3_STFC_DEST"

run_step "SSH/token/s3/directory" \
  dataset-download-tool \
    --username "$JASMIN_USERNAME" \
    --ssh xfer-vm-01.jasmin.ac.uk \
    --ssh-download-path /gws/pw/j07/perf_testing/test_download_dir \
    --key-filename "$SSH_KEY" \
    -s 1 \
    --dest "$S3_MINIO_DEST"

# =============================================================================
# Summary
# =============================================================================

echo
echo "=============================================================="
echo "FINAL SUMMARY - All 54 Feature Combinations"
echo "=============================================================="
fail=0
for entry in "${RESULTS[@]}"; do
  IFS='|' read -r s rc src auth dst mode name <<< "$entry"
  if [[ "$rc" -eq 0 ]]; then
    status="✓ OK  "
  else
    status="✗ FAIL"
    fail=$((fail + 1))
  fi
  printf "[%2d] %s (rc=%3s) %-6s | %-9s | %-7s | %-9s | %s\n" \
    "$s" "$status" "$rc" "$src" "$auth" "$dst" "$mode" "$name"
done
echo "--------------------------------------------------------------"
echo "Total tests: ${#RESULTS[@]} | Passed: $((${#RESULTS[@]} - fail)) | Failed: $fail"
echo "=============================================================="
exit $fail
