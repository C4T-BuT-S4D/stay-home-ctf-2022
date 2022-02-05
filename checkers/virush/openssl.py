#!/usr/bin/env python3

import os
import shlex
import typing
import asyncio
import hashlib
import tempfile
import contextlib


DH_PARAM_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'dhparam.pem',
)

class OpenSSL:
    TIMEOUT = 0.1
    ALGORITHM = 'aes-128-cbc'
    KEY_SIZE = 32
    BLOCK_SIZE = 16

    def __init__(self, process: asyncio.subprocess.Process) -> None:
        self.process = process

    @contextlib.asynccontextmanager
    async def create():
        process = await asyncio.create_subprocess_exec(
            'openssl',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            yield OpenSSL(process)
        finally:
            try:
                process.terminate()
                await process.wait()
            except Exception:
                pass

    async def execute(self, arguments: typing.Iterable[str]) -> None:
        command = shlex.join(arguments)

        await self.process.stdout.readexactly(len('OpenSSL> '))

        self.process.stdin.write(f'{command}{os.linesep}'.encode())
        await self.process.stdin.drain()

        await asyncio.sleep(self.TIMEOUT)

    async def generate_private_key(self) -> bytes:
        _, private_key_file = tempfile.mkstemp()

        await self.execute([
            'genpkey',
            '-paramfile', DH_PARAM_FILE,
            '-out', private_key_file,
        ])

        with open(private_key_file, 'rb') as file:
            private_key = file.read()

        os.unlink(private_key_file)

        return private_key

    async def get_public_key(self, private_key: bytes) -> bytes:
        _, private_key_file = tempfile.mkstemp()
        _, public_key_file = tempfile.mkstemp()

        with open(private_key_file, 'wb') as file:
            file.write(private_key)

        await self.execute([
            'pkey',
            '-in', private_key_file,
            '-pubout',
            '-out', public_key_file,
            '-outform', 'DER',
        ])

        with open(public_key_file, 'rb') as file:
            public_key = file.read()

        os.unlink(public_key_file)
        os.unlink(private_key_file)

        return public_key

    async def derive_shared_key(
            self, private_key: bytes, other_public_key: bytes,
    ) -> str:
        _, private_key_file = tempfile.mkstemp()
        _, other_public_key_file = tempfile.mkstemp()
        _, shared_key_file = tempfile.mkstemp()

        with open(private_key_file, 'wb') as file:
            file.write(private_key)

        with open(other_public_key_file, 'wb') as file:
            file.write(other_public_key)

        await self.execute([
            'pkeyutl',
            '-inkey', private_key_file,
            '-derive',
            '-peerkey', other_public_key_file,
            '-peerform', 'DER',
            '-out', shared_key_file,
        ])

        with open(shared_key_file, 'rb') as file:
            shared_key = file.read()

        os.unlink(shared_key_file)
        os.unlink(other_public_key_file)
        os.unlink(private_key_file)

        return shared_key, hashlib.sha256(shared_key).hexdigest()

    async def encrypt(self, plaintext: bytes, key: str) -> bytes:
        _, plaintext_file = tempfile.mkstemp()
        _, ciphertext_file = tempfile.mkstemp()

        with open(plaintext_file, 'wb') as file:
            file.write(plaintext)

        iv = os.urandom(self.BLOCK_SIZE)

        await self.execute([
            self.ALGORITHM, '-e',
            '-iter', '16',
            '-k', key,
            '-iv', iv.hex(),
            '-in', plaintext_file,
            '-out', ciphertext_file,
        ])

        with open(ciphertext_file, 'rb') as file:
            ciphertext = file.read()

        os.unlink(ciphertext_file)
        os.unlink(plaintext_file)

        return iv + ciphertext

    async def decrypt(self, ciphertext: bytes, key: str) -> bytes:
        _, ciphertext_file = tempfile.mkstemp()
        _, plaintext_file = tempfile.mkstemp()

        iv, ciphertext = (
            ciphertext[:self.BLOCK_SIZE], ciphertext[self.BLOCK_SIZE:],
        )

        with open(ciphertext_file, 'wb') as file:
            file.write(ciphertext)

        await self.execute([
            self.ALGORITHM, '-d',
            '-iter', '16',
            '-k', key,
            '-iv', iv.hex(),
            '-in', ciphertext_file,
            '-out', plaintext_file,
        ])

        with open(plaintext_file, 'rb') as file:
            plaintext = file.read()

        os.unlink(plaintext_file)
        os.unlink(ciphertext_file)

        return plaintext
