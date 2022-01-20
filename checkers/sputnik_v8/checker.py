#!/usr/bin/env python3

import sys
import requests

from checklib import *
from example_lib import *
from time import sleep


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
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error',
                       'Got requests connection error')

    def check(self):
        session = get_initialized_session()
        access_key = self.mch.get_access_key()
        opcodes, context, s = self.mch.generate_random_vm()
        execute_result = self.mch.execute(
            session, opcodes, access_key, s, Status.MUMBLE)
        report = self.mch.get_report(
            session, access_key, execute_result.vm_id, Status.MUMBLE)
        self.assert_eq(report, s, "Invalid report on /execute", Status.MUMBLE)
        self.assert_eq(execute_result.context, {
                       'CALLS': context}, "Invalid context on /execute", Status.MUMBLE)
        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        session = get_initialized_session()
        access_key = self.mch.get_access_key()
        opcodes, s = self.mch.generate_flag_vm(flag)
        execute_result = self.mch.execute(
            session, opcodes, access_key, s, Status.MUMBLE)
        self.assert_eq(execute_result.context, {
                       'CALLS': {'http.request': 2, 'Buffer.from': 2, 'JSON.stringify': 1}}, 'Invalid context on /execute', Status.MUMBLE)
        self.cquit(Status.OK, execute_result.vm_id,
                   f'{execute_result.vm_id}:{access_key}')

    def get(self, flag_id: str, flag: str, vuln: str):
        sleep(5)
        session = get_initialized_session()
        vm_id, access_key = flag_id.split(":")
        report = self.mch.get_report(
            session, access_key, vm_id, Status.MUMBLE)
        self.assert_eq(
            report, flag, "Invalid flag on /execute", Status.CORRUPT)
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
