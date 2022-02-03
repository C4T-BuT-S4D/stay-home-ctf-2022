import hashlib
import json
import os
import random

import requests

from checklib import BaseChecker
from Cryptodome.Cipher import ChaCha20

PORT = 8000


class ModelrnaLib:

    @property
    def url(self):
        return f'http://{self.host}:{self.port}/api'

    def __init__(self, checker: BaseChecker, port=PORT, host=None):
        self.c = checker
        self.port = port
        self.host = host or self.c.host
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mine_results.json'), 'r') as f:
            self.mine_answers = json.loads(f.read())

    def check_json_dict_response(self, resp, url, keys):
        err_msg = f"Invalid JSON response on {url}"
        data = self.c.get_json(resp, err_msg)
        self.c.assert_eq(type(data), dict, err_msg)
        for k in keys:
            if '.' in k:
                # Support only one level because fuck you.
                top, nested = k.split('.')
                self.c.assert_in(top, data, err_msg + f": key '{k}' is not present")
                inner_value = data[top]
                self.c.assert_eq(type(inner_value), dict, err_msg)
                self.c.assert_in(nested, inner_value, err_msg + f": key '{k}' is not present")
            else:
                self.c.assert_in(k, data, err_msg + f": key '{k}' is not present")

        return data

    def register(self, session: requests.Session, username: str, password: str, vaccine_name: str):
        resp = session.post(self.url + '/register', json={
            'username': username,
            'password': password,
            'email': username + '@cbsctf.live',
            'vaccine_name': vaccine_name
        })
        return self.check_json_dict_response(resp, "/register", ('api_token', 'user_id'))

    def login(self, session: requests.Session, username: str, password: str):
        resp = session.post(self.url + '/login', json={
            'username': username,
            'password': password
        })
        return self.check_json_dict_response(resp, "/login", ('api_token', 'user_id'))

    def list_latest_users(self, session: requests.Session):
        resp = session.get(self.url + '/users')

        data = self.c.get_json(resp, "Invalid JSON response on /users")
        self.c.assert_eq(type(data), list, "Invalid JSON response on /users")
        if data:
            elem = random.choice(data)
            self.c.assert_eq(type(elem), dict, 'Invalid JSON response on /users')
            for k in ('user_id', 'username', 'email', 'vaccine_info'):
                self.c.assert_in(k, elem, f"Invalid JSON response on /users: key '{k}' is not present")
        return data

    def get_user_info(self, session: requests.Session):
        resp = session.get(self.url + '/userinfo')
        return self.check_json_dict_response(
            resp,
            "/userinfo",
            ('user_id', 'username',
             'vaccine_info.vaccine_id', 'vaccine_info.vaccine_key', 'vaccine_info.vaccine_name')
        )

    def upload_model(self, session: requests.Session, model: bytes, enc_key: str):
        resp = session.post(self.url + '/vaccine/upload', files={'file': self.encrypt_model(model, enc_key)})
        self.c.check_response(resp, 'Failed to upload vaccine model')

    def end_to_end_prediction(self, session: requests.Session, vaccine_id, data):
        captcha_info = self.get_captcha(session)
        # answer = self.mine(captcha_info['captcha_challenge'], 5)
        answer = self.captcha_answer(captcha_info['captcha_challenge'])
        token = self.send_captcha(session, captcha_info['captcha_key'], str(answer))['captcha_token']
        return self.make_prediction(session, vaccine_id, data, token)

    def make_prediction(self, session: requests.Session, vaccine_id, data, captcha_token):
        resp = session.post(self.url + '/vaccine/' + vaccine_id + '/test',
                            json=data, headers={'X-Captcha-Token': captcha_token})
        return self.check_json_dict_response(resp, '/vaccine/' + vaccine_id + '/test',
                                             ('test_id', 'prediction', 'prediction_probability'))

    def get_test_result(self, session: requests.Session, test_id):
        resp = session.get(self.url + '/vaccine/test/' + test_id)
        return self.check_json_dict_response(resp, '/vaccine/test/<id>',
                                             ('prediction', 'prediction_probability', 'age', 'sex', 'rh', 'blood_type',
                                              'sugar_level', 'ssn'))

    def get_tests_for_vaccine(self, session: requests.Session):
        resp = session.get(self.url + '/vaccine/tests')
        data = self.c.get_json(resp, "Invalid JSON response on /vaccine/tests")
        self.c.assert_eq(type(data), list, "Invalid JSON response on /vaccine/tests")
        if data:
            elem = random.choice(data)
            for k in ('prediction', 'prediction_probability', 'age', 'sex', 'rh', 'blood_type',
                      'sugar_level', 'ssn'):
                self.c.assert_in(k, elem, f"Invalid JSON response on /vaccine/tests: key '{k}' is not present")
        return data

    def get_captcha(self, session: requests.Session):
        resp = session.get(self.url + '/captcha/get')
        return self.check_json_dict_response(resp, '/captcha/get', ('captcha_key', 'captcha_challenge'))

    def send_captcha(self, session: requests.Session, key: str, answer: str):
        resp = session.post(self.url + '/captcha/validate', json={'key': key, 'answer': answer})
        return self.check_json_dict_response(resp, '/captcha/validate', ('captcha_token',))

    def encrypt_model(self, model: bytes, enc_key: str):
        KEY_SIZE = 32
        NONCE_SIZE = 12

        if len(enc_key) != KEY_SIZE * 2 + NONCE_SIZE * 2:
            raise ValueError("invalid encryption key")
        key = b''.fromhex(enc_key[:KEY_SIZE * 2])
        cha = ChaCha20.new(key=key, nonce=b''.fromhex(enc_key[KEY_SIZE * 2:]))
        return cha.encrypt(model)

    def mine(self, message, size):
        for x in range(10 ** 100):
            s = message + str(x)
            s = s.encode()
            hsh = hashlib.sha256(s).hexdigest()
            if hsh.startswith('0' * size):
                return x

    def captcha_answer(self, message):
        answer = self.mine_answers.get(message)
        if not answer:
            return self.mine(message, 5)
        return answer
