import requests
from checklib import *
from uuid import uuid4
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum, auto, unique
from random import randint, choices
from base64 import b64encode
import re

uuid_regex = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")


@unique
class OPCODE(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    def __str__(self):
        return self.name

    OP_PUSH = auto()
    OP_POP = auto()
    OP_DUP = auto()
    OP_SWAP = auto()
    OP_HIDE = auto()
    OP_CALL = auto()
    OP_INVOKE = auto()
    OP_RESET = auto()
    OP_JMP = auto()
    OP_JMPIF = auto()
    OP_JMPNIF = auto()
    OP_REPORT = auto()
    OP_ADD = auto()
    OP_SUB = auto()
    OP_HLTCHK = auto()
    OP_HLTNCHK = auto()


class VM:
    def __init__(self):
        self.opcodes = []

    def push(self, *opcode):
        self.opcodes.append(list(opcode))

    def serialize(self) -> list:
        return [[str(opcode[0])] + opcode[1:] for opcode in self.opcodes]


@dataclass
class ExecutionResult:
    vm_id: str
    context: defaultdict(int)


class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}/api'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = 5678

    def get_access_key(self) -> str:
        return uuid4()

    def execute(self, session: requests.Session, opcodes: list, access_key: str, report: str, status: Status) -> ExecutionResult:
        response = session.post(f'{self.url}/execute', params={
            "accessKey": access_key
        }, json={
            "opcodes": opcodes,
            "report": report
        })

        data = self.c.get_json(
            response, "Invalid response on /execute", status)
        self.c.assert_eq(type(data), dict,
                         "Invalid response type on /execute", status)
        self.c.assert_in("ok", data, "No ok field on /execute", status)
        self.c.assert_eq(data["ok"], True, "Not ok on /execute", status)
        self.c.assert_in("result", data, "No result field on /execute", status)
        self.c.assert_eq(type(data["result"]), dict,

                         "Invalid result type on /execute", status)
        self.c.assert_in("vmId", data["result"],
                         "No vmId field on /execute", status)
        self.c.assert_eq(type(data["result"]["vmId"]),
                         str, "Invalid vmId type on /execute", status)
        self.c.assert_in(
            "context", data["result"], "No context field on /execute", status)
        self.c.assert_eq(type(data["result"]["context"]),
                         dict, "Invalid context type on /execute", status)
        self.c.assert_in(
            "CALLS", data["result"]["context"], "No CALLS field on /execute", status)
        self.c.assert_eq(type(data["result"]["context"]["CALLS"]),
                         dict, "Invalid CALLS type on /execute", status)
        for fn in data["result"]["context"]["CALLS"]:
            self.c.assert_eq(
                type(fn), str, "Invalid CALLS key type on /execute", status)
            self.c.assert_eq(type(
                data["result"]["context"]["CALLS"][fn]), int, "Invalid CALLS value on /execute", status)

        self.c.assert_eq(bool(uuid_regex.fullmatch(
            data["result"]["vmId"])), True, "Invalid vmId field on /execute", status)

        return ExecutionResult(data["result"]["vmId"], data["result"]["context"])

    def get_report(self, session: requests.Session, access_key: str, vm_id: str, status: Status) -> str:
        response = session.get(f'{self.url}/getReport', params={
            "accessKey": access_key,
            "vmId": vm_id
        })

        data = self.c.get_json(
            response, "Invalid response on /getReport", status)
        self.c.assert_eq(type(data), dict,
                         "Invalid response type on /getReport", status)
        self.c.assert_in("ok", data, "No ok field on /getReport", status)
        self.c.assert_eq(data["ok"], True, "Not ok on /getReport", status)
        self.c.assert_in(
            "result", data, "No result field on /getReport", status)
        self.c.assert_eq(type(data["result"]), str,

                         "Invalid result type on /getReport", status)

        self.c.assert_eq(len(data["result"]) <= 1024,
                         True, "invalid result length on /getReport")

        return data["result"]

    def generate_random_vm(self) -> (dict, dict, str):
        r = randint(0, 2)
        if r == 0:
            ops = choices([self.random_op0, self.random_op1, self.random_op2,
                          self.random_op3, self.random_op4], k=randint(20, 40))

            vm = VM()
            s = ""
            context = defaultdict(int)

            vm.push(OPCODE.OP_RESET)
            vm.push(OPCODE.OP_PUSH, "")
            for op in ops:
                ctx, ss = op(vm)
                s += ss
                for k in ctx:
                    context[k] += ctx[k]
                vm.push(OPCODE.OP_SWAP)
                vm.push(OPCODE.OP_ADD)

            vm.push(OPCODE.OP_REPORT)

            return vm.serialize(), {'http.request': 2, 'JSON.stringify': 1, **context}, s
        elif r == 1:
            vm = VM()
            s = rnd_string(100)

            vm.push(OPCODE.OP_PUSH, s)
            vm.push(OPCODE.OP_PUSH, 0)
            vm.push(OPCODE.OP_DUP)
            vm.push(OPCODE.OP_HIDE)
            vm.push(OPCODE.OP_HLTNCHK)
            vm.push(OPCODE.OP_SWAP)
            vm.push(OPCODE.OP_PUSH, 1)
            vm.push(OPCODE.OP_ADD)
            vm.push(OPCODE.OP_JMP, 6)

            return vm.serialize(), {'http.request': 2, 'JSON.stringify': 1}, s
        else:
            vm = VM()
            s = rnd_string(3)

            vm.push(OPCODE.OP_PUSH, s)
            vm.push(OPCODE.OP_PUSH, 3)

            vm.push(OPCODE.OP_PUSH, -1)
            vm.push(OPCODE.OP_ADD)
            vm.push(OPCODE.OP_SWAP)
            vm.push(OPCODE.OP_DUP)
            vm.push(OPCODE.OP_ADD)

            vm.push(OPCODE.OP_SWAP)
            vm.push(OPCODE.OP_DUP)
            vm.push(OPCODE.OP_JMPNIF, 7)

            vm.push(OPCODE.OP_POP)
            vm.push(OPCODE.OP_REPORT)

            return vm.serialize(), {'http.request': 2, 'JSON.stringify': 1}, s * 8

    def random_op0(self, vm: VM) -> (dict, str):
        s = rnd_string(10)
        vm.push(OPCODE.OP_PUSH, s)
        vm.push(OPCODE.OP_DUP)
        vm.push(OPCODE.OP_POP)
        return {}, s

    def random_op1(self, vm: VM) -> (dict, str):
        s = rnd_string(6)
        vm.push(OPCODE.OP_PUSH, 'ascii')
        vm.push(OPCODE.OP_PUSH, 1)
        vm.push(OPCODE.OP_PUSH, 'base64')
        vm.push(OPCODE.OP_PUSH, b64encode(s.encode()).decode())
        vm.push(OPCODE.OP_PUSH, 2)
        vm.push(OPCODE.OP_CALL, 'context_Buffer_from')
        vm.push(OPCODE.OP_INVOKE, 'toString')
        return {'Buffer.from': 1}, s

    def random_op2(self, vm: VM) -> (dict, str):
        s1 = rnd_string(3)
        s2 = rnd_string(3)
        s3 = rnd_string(3)
        vm.push(OPCODE.OP_PUSH, s1)
        vm.push(OPCODE.OP_PUSH, s2)
        vm.push(OPCODE.OP_PUSH, s3)
        vm.push(OPCODE.OP_HIDE)
        vm.push(OPCODE.OP_ADD)
        vm.push(OPCODE.OP_ADD)
        return {}, s2 + s1 + s3

    def random_op3(self, vm: VM) -> (dict, str):
        a = randint(-100, 100)
        b = randint(-100, 100)
        vm.push(OPCODE.OP_PUSH, a)
        vm.push(OPCODE.OP_PUSH, b)
        vm.push(OPCODE.OP_SUB)
        return {}, str(b - a)

    def random_op4(self, vm: VM) -> (dict, str):
        a = randint(1, 4)
        vm.push(OPCODE.OP_PUSH, 0)
        vm.push(OPCODE.OP_CALL, 'context_Set_constructor')
        for i in range(a):
            vm.push(OPCODE.OP_PUSH, 1)
            vm.push(OPCODE.OP_SWAP)
            vm.push(OPCODE.OP_PUSH, i)
            vm.push(OPCODE.OP_HIDE)
            vm.push(OPCODE.OP_INVOKE, 'add')
        vm.push(OPCODE.OP_PUSH, 1)
        vm.push(OPCODE.OP_CALL, 'context_Uint8Array_constructor')
        return {'Set.constructor': 1, 'Uint8Array.constructor': 1}, ",".join(map(str, range(a)))

    def generate_flag_vm(self, flag) -> (dict, str):
        vm = VM()

        s = rnd_string(100)

        vm.push(OPCODE.OP_PUSH, 1)
        vm.push(OPCODE.OP_CALL, "context_Buffer_from")
        vm.push(OPCODE.OP_PUSH, 1)
        vm.push(OPCODE.OP_PUSH, s)
        vm.push(OPCODE.OP_PUSH, 1)
        vm.push(OPCODE.OP_CALL, "context_Buffer_from")
        vm.push(OPCODE.OP_INVOKE, "equals")
        vm.push(OPCODE.OP_PUSH, "error")
        vm.push(OPCODE.OP_SWAP)
        vm.push(OPCODE.OP_HLTCHK)

        vm.push(OPCODE.OP_RESET)

        lf, rf = self.get_2_parts(flag)
        vm.push(OPCODE.OP_PUSH, rf)
        vm.push(OPCODE.OP_PUSH, lf)
        vm.push(OPCODE.OP_ADD)
        vm.push(OPCODE.OP_REPORT)

        return vm.serialize(), s

    def get_2_parts(self, s) -> (str, str):
        i = randint(1, len(s) - 1)
        return s[:i], s[i:]

    def get_substring(self, s) -> (int, int, str):
        l = randint(0, len(s))
        r = l
        while r == l:
            r = randint(0, len(s))
        if l > r:
            l, r = r, l
        return l, r, s[l:r]
