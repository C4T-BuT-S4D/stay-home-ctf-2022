import uuid
import random
import hashlib
import string

from app.storage import Storage


class CaptchaHelper:
    ALPHA = string.ascii_uppercase + string.digits
    HARDNESS = 5

    def __init__(self, storage: Storage):
        self.storage = storage

    async def create(self):
        key = str(uuid.uuid4())
        value = ''.join(random.choices(self.ALPHA, k=3))
        await self.storage.store_challenge(key, value)
        return key, value

    async def check(self, key: str, answer: str):
        challenge = await self.storage.get_challenge(key)
        if not challenge:
            raise KeyError("captcha not found or expired")

        await self.storage.revoke_challenge(key)
        hsh = hashlib.sha256(challenge + answer.encode()).hexdigest()
        return hsh.startswith('0' * self.HARDNESS)

    async def generate_token(self):
        token = str(uuid.uuid4())
        await self.storage.create_captcha_token(token)
        return token

    async def check_token(self, token):
        exists = await self.storage.check_captcha_token(token)
        if not exists:
            return False
        await self.storage.remove_captcha_token(token)
        return True
