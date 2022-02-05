#!/usr/bin/env python3

from checklib import *
import re
import grpc
import requests
from client_lib import ClientLib
from random import randint, choice
import sys

uuid_regex = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")

password_regex = re.compile(r'[a-zA-Z0-9]{,30}')


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.client_lib = ClientLib(self.host, 8980)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error',
                       'Got requests connection error')
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.cquit(Status.DOWN, 'Connection error',
                           f'Got grpc error {e.code()}: {e.details()}')
            else:
                self.cquit(Status.MUMBLE, 'Unexpected grpc error',
                           f'Got grpc error {e.code()}: {e.details()}')

    def check(self):
        user1 = self.wrap_call(self.client_lib.register,
                               "Can't register")
        user2 = self.wrap_call(self.client_lib.register,
                               "Can't register")

        auth1 = self.wrap_call(self.client_lib.login,
                               "Can't login", user1.user_id, user1.user_password)
        auth2 = self.wrap_call(self.client_lib.login,
                               "Can't login", user2.user_id, user2.user_password)

        balance1 = self.wrap_call(
            self.client_lib.balance,  "Can't get balance", auth1)
        balance2 = self.wrap_call(
            self.client_lib.balance, "Can't get balance", auth2)

        self.assert_eq(balance1, 5, "Incorrect initial balance")
        self.assert_eq(balance2, 5, "Incorrect initial balance")

        name = rnd_string(10)
        rna_info = rnd_string(32)

        private_price = randint(1, 4)
        public_price = randint(1000, 4000)

        vaccine = self.wrap_call(self.client_lib.create_vaccine,
                                 "Can't create vaccine", auth1, name, rna_info, public_price, private_price)

        got_rna_info = self.wrap_call(
            self.client_lib.buy,  "Can't buy vaccine", auth2, vaccine.private.id)

        self.assert_eq(rna_info, got_rna_info, "Incorrect rna info after buy")

        balance1 = self.wrap_call(
            self.client_lib.balance,  "Can't get balance", auth1)
        balance2 = self.wrap_call(
            self.client_lib.balance,"Can't get balance", auth2)

        self.assert_eq(balance1, 5 + private_price, "Incorrect balance after buy")
        self.assert_eq(balance2, 5 - private_price, "Incorrect balance after buy")

        price = self.wrap_call(self.client_lib.get_price,
                               "Can't get vaccine price", vaccine.private.id)

        self.assert_eq(price, private_price * 2, "Incorrect vaccine price after buy")

        got_vaccine = self.wrap_call(
            self.client_lib.get_user_vaccine,  "Can't get user vaccine", auth1)

        self.assert_eq(got_vaccine.info.name, name,
                       "Incorrect name of user vaccine")
        self.assert_eq(got_vaccine.info.seller_id, user1.user_id,
                       "Incorrect seller id of user vaccine")
        self.assert_eq(got_vaccine.info.rna_info, rna_info,
                       "Incorrect rna info of user vaccine")
        self.assert_eq(got_vaccine.private.id, vaccine.private.id,
                       "Incorrect private id of user vaccine")
        self.assert_eq(got_vaccine.private.price, private_price * 2,
                       "Incorrect private price of user vaccine")
        self.assert_eq(got_vaccine.public.id, vaccine.public.id,
                       "Incorrect public id of user vaccine")

        self.wrap_call(self.client_lib.list, "Can't list public vaccines")
        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        user1 = self.wrap_call(self.client_lib.register,
                              "Can't register")
        user2 = self.wrap_call(self.client_lib.register,
                               "Can't register")

        self.assert_eq(bool(uuid_regex.fullmatch(user1.user_id)), True, "Incorrect user id format")
        self.assert_eq(bool(uuid_regex.fullmatch(user2.user_id)), True, "Incorrect user id format")
        self.assert_eq(bool(password_regex.fullmatch(user1.user_password)), True, "Incorrect user password format")
        self.assert_eq(bool(password_regex.fullmatch(user2.user_password)), True, "Incorrect user password format")

        auth1 = self.wrap_call(self.client_lib.login,
                               "Can't login", user1.user_id, user1.user_password)

        name = rnd_string(10)

        vaccine = self.wrap_call(self.client_lib.create_vaccine,
                                 "Can't create vaccine", auth1, name, flag, choice([0.0001, 0.0002, 0.0003]), randint(133713371337))

        self.assert_eq(bool(uuid_regex.fullmatch(vaccine.public.id)), True, "Incorrect vaccine id format")
        self.assert_eq(bool(uuid_regex.fullmatch(vaccine.private.id)), True, "Incorrect vaccine id format")

        self.cquit(
            Status.OK, vaccine.public.id, f'{vaccine.private.id}:{user1.user_id}:{user1.user_password}:{user2.user_id}:{user2.user_password}')

    def get(self, flag_id: str, flag: str, vuln: str):
        vaccine_id, user1_id, user1_password, user2_id, user2_password = flag_id.split(':')

        auth1 = self.wrap_call(self.client_lib.login,
                               "Can't login", user1_id, user1_password)
        auth2 = self.wrap_call(self.client_lib.login,
                               "Can't login", user2_id, user2_password)

        vaccine = self.wrap_call(self.client_lib.get_user_vaccine, "Can't get vaccine", auth1)

        self.assert_eq(vaccine.info.rna_info, flag, "Incorrect vaccine rna info", Status.CORRUPT)

        rna_info = self.wrap_call(self.client_lib.buy, "Can't buy vaccine", auth2, vaccine.private.id)

        self.assert_eq(rna_info, flag, "Incorrect vaccine rna info after buy", Status.CORRUPT)

        self.cquit(Status.OK)

    def wrap_call(self, fn, message, *args):
        try:
            return fn(*args)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise
            self.cquit(Status.MUMBLE, message,
                       f'Got grpc error {e.code()}: {e.details()}')


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
