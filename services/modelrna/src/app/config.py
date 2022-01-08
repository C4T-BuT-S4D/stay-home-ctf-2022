import os
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    jwt_key: str = 'secret'
    uploads_folder: str = '/tmp/uploads'
    redis_host: str = '127.0.0.1'
    redis_port: str = 6379
    redis_db: int = 3

    class Config:
        env_file = "config.env"

    @property
    def redis_url(self):
        return f'redis://{self.redis_host}:{self.redis_port}/{self.redis_db}'

    @property
    def redis_celery_url(self):
        return f'redis://{self.redis_host}:{self.redis_port}/{self.redis_db + 1}'


@lru_cache()
def get_settings() -> Settings:
    return Settings()
