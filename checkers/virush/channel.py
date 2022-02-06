#!/usr/bin/env python3

import os
import abc
import base64
import contextlib
import websockets.client as ws

import openssl


class ChannelException(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self) -> str:
        return f'channel error: {self.message}'


class Channel(abc.ABC):
    @abc.abstractmethod
    async def sendline(self, line: str) -> None:
        pass

    @abc.abstractclassmethod
    async def recvline(self) -> str:
        pass


class WebsocketChannel(Channel):
    def __init__(self, connection: ws.WebSocketClientProtocol) -> None:
        self.connection = connection

    @contextlib.asynccontextmanager
    async def create(uri: str, user_agent: str = ''):
        headers = {
            'User-Agent': user_agent,
        }

        async with ws.connect(uri, extra_headers=headers) as connection:
            try:
                yield WebsocketChannel(connection)
            finally:
                try:
                    await connection.close()
                except Exception:
                    pass

    async def sendline(self, line: str) -> None:
        await self.connection.send(line)

    async def recvline(self) -> str:
        response = await self.connection.recv()

        if not isinstance(response, str):
            raise ChannelException('invalid websocket mode')

        return str(response)


class EncryptedChannel(Channel):
    def __init__(
            self, channel: Channel, openssl: openssl.OpenSSL,
    ) -> None:
        self.channel = channel
        self.openssl = openssl
        self.shared_key: str = None

    async def establish(self) -> None:
        other_public_key = await self.channel.recvline()

        try:
            other_public_key = base64.b64decode(other_public_key)
        except Exception:
            raise ChannelException('base64 error')

        private_key = await self.openssl.generate_private_key()

        if len(private_key) == 0:
            raise Exception('failed to generate private key')

        my_public_key = await self.openssl.get_public_key(private_key)

        if len(my_public_key) == 0:
            raise Exception('failed to get public key')

        my_public_key = base64.b64encode(my_public_key).decode()

        key, self.shared_key = await self.openssl.derive_shared_key(
            private_key, other_public_key,
        )

        if len(key) == 0 or len(self.shared_key) < self.openssl.KEY_SIZE:
            raise ChannelException('derive shared key error')

        await self.channel.sendline(my_public_key)

    async def sendline(self, line: str) -> None:
        if self.shared_key is None:
            raise Exception('channel is not established')

        line += os.linesep

        ciphertext = await self.openssl.encrypt(
            line.encode(), self.shared_key,
        )

        data = base64.b64encode(ciphertext).decode()

        await self.channel.sendline(data)

    async def recvline(self) -> str:
        if self.shared_key is None:
            raise Exception('channel is not established')

        data = await self.channel.recvline()

        try:
            ciphertext = base64.b64decode(data)
        except Exception:
            raise ChannelException('base64 error')

        plaintext = await self.openssl.decrypt(
            ciphertext, self.shared_key
        )

        if len(plaintext) == 0:
            raise ChannelException('decryption error')

        try:
            line = plaintext.decode()
        except Exception:
            raise ChannelException('decoding error')

        return line.strip(os.linesep)
