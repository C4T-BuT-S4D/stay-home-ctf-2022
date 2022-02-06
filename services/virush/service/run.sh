#!/bin/sh

while true; do
    websocketd --port 31337 --loglevel error \
        timeout -k 60 -s USR1 300 \
            /var/virush/server \
    | stdbuf -i0 -o0 -e0 \
        cut -d '|' -f 5-
done
