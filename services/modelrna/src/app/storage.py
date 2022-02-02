import json
import logging
import uuid
from hashlib import sha1

import aioredis


class Storage(object):
    USERS_SET = 'users'
    USER_LOGINS_SET = 'user-logins'
    LATEST_USERS_LIST = 'latest-users'
    VACCINE_TEST_IDS_LIST_PREFIX = 'vaccine-test-ids'
    VACCINE_TESTS_SET = 'vaccine-tests'
    CAPTCHA_CHALLENGES_PREFIX = 'captcha-challenges'
    CAPTCHA_TOKENS_PREFIX = 'captcha-tokens'

    def __init__(self, redis_cli: aioredis.Redis):
        self.redis_cli = redis_cli

    @classmethod
    def uuid(cls):
        return str(uuid.uuid4())

    @classmethod
    def hash_pwd(cls, x):
        return sha1(x.encode(errors='ignore')).hexdigest()

    async def user_exists(self, user_id=None, username=None):
        if user_id:
            return await self.redis_cli.hexists(self.USERS_SET, user_id)
        if username:
            return await self.redis_cli.hexists(self.USER_LOGINS_SET, username)
        raise ValueError("Storage.user_exists(): No user_id or login provided")

    async def find_user(self, user_id=None, username=None):
        val = None
        if user_id:
            val = await self.redis_cli.hget(self.USERS_SET, user_id)
        elif username:
            val = await self.redis_cli.hget(self.USER_LOGINS_SET, username)
        else:
            raise ValueError("Storage.find_user(): No user_id or login provided")
        if val:
            try:
                val = json.loads(val)
            except Exception as e:
                logging.error('Corrupted userdata "{}" with error = {}'.format(val, e))
        return val

    async def add_user(self, username, password, email, vaccine_info):
        uid = self.uuid()

        lock_string = f'LOCK_USERS_{username}'

        user_data = json.dumps(
            {'user_id': uid,
             'username': username,
             'password': password,
             'email': email,
             'vaccine_info': vaccine_info
             })

        public_info = json.dumps({
            'user_id': uid,
            'username': username,
            'email': email,
            'vaccine_info': {
                'name': vaccine_info['vaccine_name'],
                'id': vaccine_info['vaccine_id'],
            },
        })

        try:
            async with self.redis_cli.pipeline(transaction=False) as tx:
                await tx.watch(lock_string)
                # Start the TX.
                tx.multi()
                await tx.hset(self.USER_LOGINS_SET, username, user_data)
                await tx.hset(self.USERS_SET, uid, user_data)
                # Finish the TX.
                await tx.incr(lock_string)
                await tx.rpush(self.LATEST_USERS_LIST, public_info)
                await tx.execute()

        except aioredis.WatchError as e:
            logging.error("TX failed (possible race): {}".format(e))
            raise e
        except Exception as e:
            logging.error('Unexpected error: {}'.format(e))
            raise e
        return uid

    async def latest_users(self, limit=500):
        try:
            users = await self.redis_cli.lrange(self.LATEST_USERS_LIST, -limit - 1, -1)
            out = []
            for rec in users:
                out.append(json.loads(rec.decode()))
            return out[::-1]
        except Exception as e:
            logging.error("Storage.latest_users(): {}".format(str(e)))
            return []

    # # # Test functions # # #
    async def save_vaccine_test(self, vaccine_id, test_id, test_data):
        try:
            await self.redis_cli.hset(self.VACCINE_TESTS_SET, test_id, json.dumps(test_data))
            await self.redis_cli.lpush(self.VACCINE_TEST_IDS_LIST_PREFIX + ":" + vaccine_id, test_id)
        except Exception as e:
            logging.error("Storage.save_vaccine_test(): {}".format(str(e)))
            raise e

    async def get_vaccine_test(self, test_id):
        try:
            return json.loads(await self.redis_cli.hget(self.VACCINE_TESTS_SET, test_id))
        except Exception as e:
            logging.error("Storage.get_vaccine_test(): {}".format(str(e)))
            raise e

    async def get_tests_for_vaccine(self, vaccine_id):
        try:
            keys = await self.redis_cli.lrange(self.VACCINE_TEST_IDS_LIST_PREFIX + ":" + vaccine_id, 0, -1)
            results = []
            for key in keys:
                try:
                    results.append(await self.get_vaccine_test(key))
                except Exception as e:
                    logging.error('failed to get test_data by id "{}": {}'.format(key, str(e)))
            return results
        except Exception as e:
            logging.error("Storage.get_tests_for_vaccine(): {}".format(str(e)))
            raise e

    # # # Captcha functions # # #
    async def store_challenge(self, chal_id, value, ttl=60):
        try:
            await self.redis_cli.set(self.CAPTCHA_CHALLENGES_PREFIX + ':' + chal_id, value, ex=ttl)
        except Exception as e:
            logging.error("failed to create captcha key: {}".format(str(e)))
            raise e

    async def get_challenge(self, chal_id) -> bytes:
        try:
            return await self.redis_cli.get(self.CAPTCHA_CHALLENGES_PREFIX + ":" + chal_id)
        except Exception as e:
            logging.error("failed to get captcha key: {}".format(str(e)))
            raise e

    async def revoke_challenge(self, chal_id):
        try:
            await self.redis_cli.delete(self.CAPTCHA_CHALLENGES_PREFIX + ":" + chal_id)
            logging.error("DELETED captcha")
        except Exception as e:
            logging.error("failed to delete captcha key: {}".format(str(e)))
            raise e

    async def create_captcha_token(self, key, ttl=30):
        try:
            await self.redis_cli.set(self.CAPTCHA_TOKENS_PREFIX + ":" + key, '1', ex=ttl)
        except Exception as e:
            logging.error("failed to create captcha token: {}".format(str(e)))
            raise e

    async def check_captcha_token(self, key):
        try:
            return await self.redis_cli.exists(self.CAPTCHA_TOKENS_PREFIX + ":" + key)
        except Exception as e:
            logging.error("failed to create captcha token: {}".format(str(e)))
            raise e

    async def remove_captcha_token(self, key):
        try:
            await self.redis_cli.delete(self.CAPTCHA_TOKENS_PREFIX + ":" + key)
        except Exception as e:
            logging.error("failed to delete captcha token: {}".format(str(e)))
            raise e
