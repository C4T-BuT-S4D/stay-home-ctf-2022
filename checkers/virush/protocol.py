#!/usr/bin/env python3

import enum
import typing

import channel


class ProtocolException(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self) -> str:
        return f'protocol error: {self.message}'


class PingResponse(enum.Enum):
    SUCCESS = enum.Enum()


class RegisterResponse(enum.Enum):
    ALREADY_REGISTERED = enum.auto()
    SUCCESS = enum.auto()


class LoginResponse(enum.Enum):
    DOES_NOT_EXIST = enum.auto()
    INVALID_PASSWORD = enum.auto()
    SUCCESS = enum.auto()


class LogoutResponse(enum.Enum):
    SUCCESS = enum.auto()


class GetResponse(enum.Enum):
    USER_DOES_NOT_EXIST = enum.auto()
    PROPERTY_DOES_NOT_EXIST = enum.auto()
    SUCCESS = enum.auto()


class PutResponse(enum.Enum):
    WRONG_USER = enum.auto()
    USER_DOES_NOT_EXIST = enum.auto()
    PROPERTY_ALREADY_EXISTS = enum.auto()
    SUCCESS = enum.auto()


class ExitResponse(enum.Enum):
    SUCCESS = enum.auto()


class VirushProtocol:
    def __init__(self, channel: channel.Channel) -> None:
        self.channel = channel

    async def ping(self) -> PingResponse:
        await self.channel.sendline(f'PING')

        response = await self.channel.recvline()

        if response == f'SUCCESS: PONG':
            return PingResponse.SUCCESS

        raise ProtocolException('wrong response for ping')

    async def register(self, username: str, password: str) -> RegisterResponse:
        await self.channel.sendline(f'REGISTER')
        await self.channel.sendline(f'{username} {password}')

        response = await self.channel.recvline()

        if response == f'ERROR: USER {username} IS ALREADY REGISTERED':
            return RegisterResponse.ALREADY_REGISTERED
        elif response == f'SUCCESS: USER {username} HAS BEEN REGISTERED':
            return RegisterResponse.SUCCESS

        raise ProtocolException('wrong response for register')

    async def login(self, username: str, password: str) -> LoginResponse:
        await self.channel.sendline(f'LOGIN')
        await self.channel.sendline(f'{username} {password}')

        response = await self.channel.recvline()

        if response == f'ERROR: USER {username} DOES NOT EXIST':
            return LoginResponse.DOES_NOT_EXIST
        elif response == f'ERROR: INVALID PASSWORD FOR USER {username}':
            return LoginResponse.INVALID_PASSWORD
        elif response == f'SUCCESS: LOGGED IN AS {username}':
            return LoginResponse.SUCCESS

        raise ProtocolException('wrong response for login')

    async def logout(self) -> LogoutResponse:
        await self.channel.sendline(f'LOGOUT')

        response = await self.channel.recvline()

        if response == f'SUCCESS: LOGGED OUT':
            return LogoutResponse.SUCCESS

        raise ProtocolException('wrong response for logout')

    async def get(
            self, username: str, property_name: str, encrypted: bool,
    ) -> typing.Tuple[GetResponse, str]:
        mode = 'ENCRYPTED' if encrypted else ''

        await self.channel.sendline(f'GET')
        await self.channel.sendline(f'{username} {property_name} {mode}')

        response = await self.channel.recvline()

        if response == f'ERROR: USER {username} DOES NOT EXIST':
            result = GetResponse.USER_DOES_NOT_EXIST
        elif response == f'ERROR: {property_name} DOES NOT EXIST FOR USER {username}':
            result = GetResponse.PROPERTY_DOES_NOT_EXIST
        elif response == f'SUCCESS: TRYING TO GET {property_name} FROM USER {username}':
            result = GetResponse.SUCCESS
        else:
            raise ProtocolException('wrong response for get')

        return result, await self.channel.recvline()

    async def put(
            self, username: str, property_name: str, encrypted: bool, data: str = '',
    ) -> PutResponse:
        mode = 'ENCRYPTED' if encrypted else ''

        await self.channel.sendline(f'PUT')
        await self.channel.sendline(f'{username} {property_name} {mode}')

        response = await self.channel.recvline()

        if response == f'ERROR: YOU ARE NOT {username}':
            return PutResponse.WRONG_USER
        elif response == f'ERROR: USER {username} DOES NOT EXIST':
            return PutResponse.USER_DOES_NOT_EXIST
        elif response == f'ERROR: {property_name} ALREADY EXISTS FOR USER {username}':
            return PutResponse.PROPERTY_ALREADY_EXISTS
        elif response == f'SUCCESS: TRYING TO PUT {property_name} TO USER {username}':
            result = PutResponse.SUCCESS
        else:
            raise ProtocolException('wrong response for put')
 
        await self.channel.sendline(data)

        return result

    async def exit(self) -> None:
        await self.channel.sendline(f'EXIT')

        response = await self.channel.recvline()

        if response == f'SUCCESS: BYE':
            return ExitResponse.SUCCESS

        raise ProtocolException('wrong response for exit')
