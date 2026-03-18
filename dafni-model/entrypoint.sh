#!/bin/sh

if [ -f /data/inputs/args.env ]; then
  export $(grep -v '^#' /data/inputs/args.env | xargs)
fi

ceda-download-tool \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --url "$URL" \
    --dest "/data/outputs/" \
    --checksum 