#!/usr/bin/env python3

import sys
import select
import asyncio
import contextlib

import openssl
import channel


@contextlib.asynccontextmanager
async def make_connection(uri: str):
    async with openssl.OpenSSL.create() as ssl:
        async with channel.WebsocketChannel.create(uri) as ws:
            _channel = channel.EncryptedChannel(ws, ssl)
            await _channel.establish()

            yield _channel


async def main(host: str) -> None:
    uri = f'ws://{host}:17171/api'

    async with make_connection(uri) as channel:
        while True:
            has_input, *_ = select.select([sys.stdin], [], [], 1)

            if has_input:
                request = sys.stdin.readline().strip()
                await channel.sendline(request)

            try:
                response = await asyncio.wait_for(channel.recvline(), 1)
                print(response)
            except asyncio.TimeoutError:
                pass


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1]))
