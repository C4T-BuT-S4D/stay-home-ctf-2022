#!/bin/sh

while true; do
    date -uR

    find "/tmp/keys_directory/" \
        -type f \
        -and -not -newermt "-1800 seconds" \
        -delete

    find "/tmp/storage_directory/" \
        -type d \
        -and -not -path "/tmp/storage_directory/" \
        -and -not -newermt "-1800 seconds" \
        -exec rm -r {} +

    sleep 60
done
