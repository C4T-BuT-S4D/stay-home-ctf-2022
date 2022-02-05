#!/usr/bin/env python3

import sys
import json
import typing
import asyncio
import hashlib
import traceback
import contextlib
import dataclasses
import checklib.status as checklib
import checklib.generators as generators
import websockets.exceptions

import openssl
import channel
import protocol


@dataclasses.dataclass
class Verdict:
    status: checklib.Status
    public: str = ''
    private: typing.Optional[str] = None

    def __post_init__(self) -> None:
        assert type(self.status) == checklib.Status

        if self.private is None:
            self.private = self.public


class Checker:
    vulns: int = 2
    timeout: int = 59
    uses_attack_data: bool = True

    def __init__(self, host: str) -> None:
        self.host = host
        self.port = 17171
        self.uri = f'ws://{self.host}:{self.port}/api/'

    @contextlib.asynccontextmanager
    async def initialize(self):
        async with openssl.OpenSSL.create() as ssl:
            async with channel.WebsocketChannel.create(self.uri, 'checker') as ws:
                _channel = channel.EncryptedChannel(ws, ssl)
                await _channel.establish()

                proto = protocol.VirushProtocol(_channel)
                yield ssl, proto

                await proto.exit()

    async def action(self, action: str, *args, **kwargs) -> Verdict:
        try:
            if action == 'info':
                return await self.info(*args, **kwargs)
            elif action == 'check':
                return await self.check(*args, **kwargs)
            elif action == 'put':
                return await self.put(*args, **kwargs)
            elif action == 'get':
                return await self.get(*args, **kwargs)
            else:
                return Verdict(checklib.Status.ERROR, 'checker failed', f'invalid action: {action}')
        except (protocol.ProtocolException, channel.ChannelException) as error:
            return Verdict(checklib.Status.MUMBLE, str(error))
        except websockets.exceptions.ConnectionClosed as error:
            return Verdict(checklib.Status.MUMBLE, 'connection has been closed unexpectedly', str(error))
        except websockets.exceptions.WebSocketException as error:
            return Verdict(checklib.Status.DOWN, 'websocket error', str(error))
        except asyncio.exceptions.TimeoutError as error:
            return Verdict(checklib.Status.DOWN, 'timeout error', str(error))
        except ConnectionError as error:
            return Verdict(checklib.Status.DOWN, 'connection error', str(error))
        except Exception:
            return Verdict(checklib.Status.ERROR, 'checker failed', traceback.format_exc())

    async def info(self) -> Verdict:
        data = {
            'vulns': self.vulns,
            'timeout': self.timeout,
            'attack_data': self.uses_attack_data,
        }

        return Verdict(checklib.Status.OK, json.dumps(data))

    async def check(self) -> Verdict:
        # TODO: add more checks for all handlers

        async with self.initialize() as _:
            pass

        return Verdict(checklib.Status.OK)

    async def put(self, _: str, flag: str, vuln: str) -> Verdict:
        username = generators.rnd_username(10)
        password = generators.rnd_password(70)

        async with self.initialize() as (_, proto):
            response = await proto.register(username, password)
            if response is not protocol.RegisterResponse.SUCCESS:
                return Verdict(checklib.Status.MUMBLE, 'failed to register', response)

            response = await proto.login(username, password)
            if response is not protocol.LoginResponse.SUCCESS:
                return Verdict(checklib.Status.MUMBLE, 'failed to login', response)

            if vuln == '1':
                verdict = await self.put_1(proto, flag, username, password)
            elif vuln == '2':
                verdict = await self.put_2(proto, flag, username, password)
            else:
                raise Exception(f'invalid vuln {vuln} in put')

            response = await proto.logout()
            if response is not protocol.LogoutResponse.SUCCESS:
                return Verdict(checklib.Status.MUMBLE, 'failed to logout', response)

            return verdict

    async def put_1(
            self,
            proto: protocol.VirushProtocol,
            flag: str,
            username: str,
            password: str,
    ) -> Verdict:
        property_name = 'flag'  # constant

        response = await proto.put(username, property_name, True, flag)
        if response is not protocol.PutResponse.SUCCESS:
            return Verdict(checklib.Status.MUMBLE, 'failed to put', response)

        attack_data = json.dumps({
            'username': username,
            'sha256(flag)': hashlib.sha256(flag.encode()).hexdigest(),
        })

        checker_data = json.dumps({
            'username': username,
            'password': password,
            'property_name': property_name,
        })

        return Verdict(checklib.Status.OK, attack_data, checker_data)

    async def put_2(
            self,
            proto: protocol.VirushProtocol,
            flag: str,
            username: str,
            password: str,
    ) -> Verdict:
        property_name = generators.rnd_string(50)

        response = await proto.put(username, property_name, False, flag)
        if response is not protocol.PutResponse.SUCCESS:
            return Verdict(checklib.Status.MUMBLE, 'failed to put', response)

        attack_data = json.dumps({
            'username': username,
            'sha256(flag)': hashlib.sha256(flag.encode()).hexdigest(),
        })

        checker_data = json.dumps({
            'username': username,
            'password': password,
            'property_name': property_name,
        })

        return Verdict(checklib.Status.OK, attack_data, checker_data)

    async def get(self, flag_id: str, flag: str, vuln: str) -> Verdict:
        checker_data = json.loads(flag_id)
        username, password, property_name = map(
            checker_data.get, ['username', 'password', 'property_name'],
        )

        async with self.initialize() as (_, proto):
            if vuln == '1':
                verdict = await self.get_1(proto, flag, username, password)
            elif vuln == '2':
                verdict = await self.get_2(proto, flag, username, property_name)
            else:
                raise Exception(f'invalid vuln {vuln} in get')

            return verdict

    async def get_1(
            self,
            proto: protocol.VirushProtocol,
            flag: str,
            username: str,
            password: str,
    ) -> Verdict:
        property_name = 'flag'  # constant

        response = await proto.login(username, password)
        if response is not protocol.LoginResponse.SUCCESS:
            return Verdict(checklib.Status.CORRUPT, 'failed to login', response)

        response, property = await proto.get(username, property_name, True)
        if response is not protocol.GetResponse.SUCCESS:
            return Verdict(checklib.Status.CORRUPT, 'failed to get', response)

        response = await proto.logout()
        if response is not protocol.LogoutResponse.SUCCESS:
            return Verdict(checklib.Status.MUMBLE, 'failed to logout', response)

        if property != flag:
            return Verdict(
                checklib.Status.CORRUPT, 'invalid flag', f'{repr(property)} != {repr(flag)}',
            )

        return Verdict(checklib.Status.OK)

    async def get_2(
            self,
            proto: protocol.VirushProtocol,
            flag: str,
            username: str,
            property_name: str,
    ) -> Verdict:
        response, property = await proto.get(username, property_name, False)
        if response is not protocol.GetResponse.SUCCESS:
            return Verdict(checklib.Status.CORRUPT, 'failed to get', response)

        if property != flag:
            return Verdict(
                checklib.Status.CORRUPT, 'invalid flag', f'{repr(property)} != {repr(flag)}',
            )

        return Verdict(checklib.Status.OK)


async def main():
    action, host, *arguments = sys.argv[1:]

    checker = Checker(host)
    verdict = await checker.action(action, *arguments)

    print(verdict.public, file=sys.stdout)
    print(verdict.private, file=sys.stderr)

    sys.exit(verdict.status.value)


if __name__ == '__main__':
    asyncio.run(main())
