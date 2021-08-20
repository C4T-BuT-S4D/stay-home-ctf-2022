#!/usr/bin/env python3

import sys
import requests

ip = sys.argv[1]
hint = sys.argv[2]

url = f"http://{ip}:1337/get_note"

r = requests.post(url, json={
    "name": hint,
})

print(r.json()["note"], flush=True)
