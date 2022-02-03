import hashlib

import requests
from Cryptodome.Cipher import ChaCha20


class ApiHelper:
    PORT = 8000

    def __init__(self, host, api_token):
        self.base_url = f'http://{host}:{self.PORT}/api'
        self.api_token = api_token

    def upload_model(self, vaccine_key, model_path):
        vaccine_key = vaccine_key
        with open(model_path, 'rb') as f:
            encrypted_model = self._encrypt_model(f.read(), vaccine_key)
            return self._upload_model(encrypted_model)

    def _encrypt_model(self, model_bytes, model_key):
        KEY_SIZE = 32
        NONCE_SIZE = 12

        if len(model_key) != KEY_SIZE * 2 + NONCE_SIZE * 2:
            raise ValueError("invalid encryption key")
        key = b''.fromhex(model_key[:KEY_SIZE * 2])
        print(list(key))
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


PATH_TO_MODEL = "sample_model.onnx"
API_TOKEN = "<your_api_token>"
VACCINE_KEY = "<your_vaccine_key>"
HOST = "localhost"

client = ApiClient(HOST, API_TOKEN)
response = client.upload_model(VACCINE_KEY, PATH_TO_MODEL)
print(response)
