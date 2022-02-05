#!/usr/bin/env python3

import sys
import os
import copy

from hashlib import md5

from checklib import *
from time import sleep

argv = copy.deepcopy(sys.argv)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kuar_lib import *

def get_name():
    return rnd_string(12)

def get_password():
    return rnd_string(24)

def gen_profile():
    data = []
    for i in range(6):
        data.append(os.urandom(19).hex())
    return data

class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except socket.error as err:
            self.cquit(Status.DOWN, 'Connection error',
                       'Got requests connection error, err: {}'.format(err))

    def check(self):
        # make connection and send keys
        self.mch.connection()
        self.mch.register(get_name(), get_password())
        profile = gen_profile()
        self.mch.update_profile(('|'.join(profile)).encode())
        data = self.mch.view_profile().decode()

        for i in profile:
            if i not in data:
                self.cquit(Status.MUMBLE, 'Profile data is incorrect!',
                       'Can\'t find my data in viewed profile')

        qr_data = self.mch.get_qr(Status.MUMBLE)
        
        for i in profile:
            if i not in qr_data.decode():
                self.cquit(Status.MUMBLE, 'QR-code is incorrect!',
                       'Can\'t find my data in qr-code')

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        self.mch.connection()
        
        username = get_name()
        password = get_password()
        self.mch.register(username, password)
        
        profile = gen_profile()
        profile[-1] = flag
        self.mch.update_profile(('|'.join(profile)).encode())

        data = self.mch.view_profile().decode()
        for i in profile:
            if i not in data:
                self.cquit(Status.MUMBLE, 'Profile data is incorrect!',
                       'Can\'t find my data in viewed profile')

        qr_data = self.mch.get_qr(Status.MUMBLE)
        for i in profile:
            if i not in qr_data.decode():
                self.cquit(Status.MUMBLE, 'QR-code is incorrect!',
                       'Can\'t find my data in qr-code')
    
        profile[-1] = get_name()
        self.mch.update_profile(('|'.join(profile)).encode())
        
        self.cquit(Status.OK, username,
                   f'{username}:{password}')

    def get(self, flag_id: str, flag: str, vuln: str):
        self.mch.connection()
        username, password = flag_id.split(":")
        self.mch.login(username, password)
        qr_data = self.mch.get_qr(Status.CORRUPT)
        
        if flag not in qr_data.decode():
            self.cquit(Status.CORRUPT, "QR-code does not contain flag",
                "QR-code does not contain flag")
        
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(argv[2])

    try:
        c.action(argv[1], *argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)