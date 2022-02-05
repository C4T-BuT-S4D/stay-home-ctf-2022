#!/usr/bin/env python3

import sys
from client_lib import ClientLib
from checklib import *

ip = sys.argv[1]
hint = sys.argv[2]

h, p = ip.split(':')
c = ClientLib(h, int(p))

user1 = c.register()
auth1 = c.login(user1.user_id, user1.user_password)

name = rnd_string(10)
rna_info = rnd_string(10)

vaccine = c.create_vaccine(auth1, name, rna_info, float('nan'))

user2 = c.register()
auth2 = c.login(user2.user_id, user2.user_password)

c.buy(auth2, vaccine.private.id)

print(c.buy(auth2, hint))
