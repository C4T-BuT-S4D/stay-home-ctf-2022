#!/bin/bash

while true; do
    socat TCP-LISTEN:1337,reuseaddr,fork,keepalive EXEC:./kuar-server
done;