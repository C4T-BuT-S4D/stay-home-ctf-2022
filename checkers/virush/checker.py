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


def print_diff(expected: typing.Any, actual: typing.Any) -> str:
    expected, actual = map(str, (expected, actual))
    max_length = 2 * len(expected)

    return f'{expected} != {actual[:max_length]}'


async def check_protocol_response(
        coroutine: typing.Coroutine, expected_response: typing.Any, error_message: str,
) -> None:
    response = await coroutine

    if isinstance(response, typing.Tuple):
        response, *_ = response

    if response is not expected_response:
        raise protocol.ProtocolException(error_message, print_diff(expected_response, response))


class Checker:
    vulns: int = 2
    timeout: int = 59
    uses_attack_data: bool = True

    def __init__(self, host: str, openssl: openssl.OpenSSL) -> None:
        self.host = host
        self.port = 17171
        self.uri = f'ws://{self.host}:{self.port}/api/'
        self.openssl = openssl

    @contextlib.asynccontextmanager
    async def create(host: str):
        async with openssl.OpenSSL.create() as ssl:
            yield Checker(host, ssl)

    @contextlib.asynccontextmanager
    async def connection(self, user_agent: str = 'checker'):
        async with channel.WebsocketChannel.create(self.uri, user_agent) as ws:
            _channel = channel.EncryptedChannel(ws, self.openssl)
            await _channel.establish()

            proto = protocol.VirushProtocol(_channel)
            yield proto

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
        except protocol.ProtocolException as error:
            return Verdict(checklib.Status.MUMBLE, error.message, error.response)
        except channel.ChannelException as error:
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
        username1 = generators.rnd_username(10)
        password1 = generators.rnd_password(70)

        username2 = generators.rnd_username(10)
        password2 = generators.rnd_password(70)

        property_name1 = generators.rnd_string(50)
        property_name2 = generators.rnd_string(50)

        value1 = generators.rnd_string(20)
        value2 = generators.rnd_string(20)

        async with self.connection() as proto:
            await check_protocol_response(
                proto.ping(), protocol.PingResponse.SUCCESS, 'failed to ping',
            )
            await check_protocol_response(
                proto.login(username1, password1), protocol.LoginResponse.DOES_NOT_EXIST, 'incorrect login behaviour',
            )
            await check_protocol_response(
                proto.register(username1, password1), protocol.RegisterResponse.SUCCESS, 'failed to register',
            )
            await check_protocol_response(
                proto.register(username1, password1), protocol.RegisterResponse.ALREADY_REGISTERED, 'incorrect register behaviour',
            )
            await check_protocol_response(
                proto.login(username1, password2), protocol.LoginResponse.INVALID_PASSWORD, 'incorrect login behaviour',
            )
            await check_protocol_response(
                proto.login(username1, password1), protocol.LoginResponse.SUCCESS, 'failed to login',
            )
            await check_protocol_response(
                proto.put(username2, property_name1, True, value1), protocol.PutResponse.WRONG_USER, 'incorrect put behaviour',
            )
            await check_protocol_response(
                proto.put(username1, property_name1, True, value1), protocol.PutResponse.SUCCESS, 'failed to put',
            )
            await check_protocol_response(
                proto.put(username1, property_name1, True, value2), protocol.PutResponse.PROPERTY_ALREADY_EXISTS, 'incorrect put behaviour',
            )
            await check_protocol_response(
                proto.get(username2, property_name1, False), protocol.GetResponse.USER_DOES_NOT_EXIST, 'incorrect get behaviour',
            )
            await check_protocol_response(
                proto.get(username1, property_name2, True), protocol.GetResponse.PROPERTY_DOES_NOT_EXIST, 'incorrect get behaviour',
            )
            await check_protocol_response(
                proto.get(username1, property_name1, True), protocol.GetResponse.SUCCESS, 'failed to get',
            )
            await check_protocol_response(
                proto.logout(), protocol.LogoutResponse.SUCCESS, 'failed to logout',
            )
            await check_protocol_response(
                proto.get(username1, property_name1, False), protocol.GetResponse.SUCCESS, 'failed to get',
            )

        return Verdict(checklib.Status.OK)

    async def put(self, _: str, flag: str, vuln: str) -> Verdict:
        username = generators.rnd_username(10)
        password = generators.rnd_password(70)

        async with self.connection() as proto:
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
            'username': username, 'password': password,
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
            'username': username, 'property_name': property_name,
        })

        return Verdict(checklib.Status.OK, attack_data, checker_data)

    async def get(self, flag_id: str, flag: str, vuln: str) -> Verdict:
        checker_data: typing.Dict[str, typing.Any] = json.loads(flag_id)

        async with self.connection() as proto:
            if vuln == '1':
                return await self.get_1(proto, flag, **checker_data)
            elif vuln == '2':
                return await self.get_2(proto, flag, **checker_data)
            else:
                raise Exception(f'invalid vuln {vuln} in get')

    async def get_1(
            self,
            proto: protocol.VirushProtocol,
            flag: str,
            username: str,
            password: str
    ) -> Verdict:
        property_name = 'flag'  # constant

        response, encrypted_flag = await proto.get(username, property_name, False)
        if response is not protocol.GetResponse.SUCCESS:
            return Verdict(checklib.Status.CORRUPT, 'failed to get', response)

        try:
            ciphertext = bytes.fromhex(encrypted_flag)
        except Exception:
            return Verdict(checklib.Status.MUMBLE, 'incorrect storage encoding')

        plaintext = await self.openssl.decrypt(ciphertext, password)
        if len(plaintext) == 0:
            return Verdict(checklib.Status.MUMBLE, 'incorrect storage encryption')

        if plaintext.strip(b'\n') != flag.encode():
            return Verdict(
                checklib.Status.CORRUPT, 'invalid flag', print_diff(flag, plaintext),
            )

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
                checklib.Status.CORRUPT, 'invalid flag', print_diff(flag, property),
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
                checklib.Status.CORRUPT, 'invalid flag', print_diff(flag, property),
            )

        return Verdict(checklib.Status.OK)


async def main():
    action, host, *arguments = sys.argv[1:]

    async with Checker.create(host) as checker:
        verdict = await checker.action(action, *arguments)

    print(verdict.public, file=sys.stdout)
    print(verdict.private, file=sys.stderr)

    sys.exit(verdict.status.value)


if __name__ == '__main__':
    asyncio.run(main())
