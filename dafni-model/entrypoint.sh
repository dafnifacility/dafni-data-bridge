#!/bin/sh

ceda-download-tool \
    -u "$USERNAME" \
    -p "$PASSWORD" \
    --url "$URL" \
    --dest "$DEST" \
    --checksum --debug