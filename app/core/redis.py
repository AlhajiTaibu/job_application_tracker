import ssl

from redis.asyncio import Redis
from typing import Optional
from app.core.config import settings
from app.core.logging_config import logger


class RedisManager:
    def __init__(self) -> None:
        self.redis_host = settings.redis_host
        self.password = settings.redis_password
        self.redis_port = settings.redis_port
        self.redis_user = settings.redis_user
        self.redis_client: Optional[Redis] = None

    async def init_redis(self):
        if self.redis_client is None:
            self.redis_client = Redis(
                host=self.redis_host,
                password=self.password,
                port=self.redis_port,
                username=self.redis_user,
                db=0,
                decode_responses=settings.is_prod,
                socket_connect_timeout=15,
                socket_keepalive=True,
                socket_timeout=15,
                retry_on_timeout=True,
                ssl=settings.is_prod,
                max_connections=50,
                ssl_cert_reqs=ssl.CERT_NONE,
                health_check_interval=30
            )
        return self.redis_client

    async def close_redis(self):
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None

    async def get_client(self):
        if self.redis_client is None:
            await self.init_redis()
        return self.redis_client

    async def set_value(self, key: str, value: str, expire_time: int = 3600):
        try:
            client = await self.get_client()
            await client.setex(key, expire_time, value)
        except Exception as error:
            logger.error(error)

    async def get_value(self, key: str):
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as error:
            logger.error(error)
            return None

    async def delete_key(self, key: str):
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as error:
            logger.error(error)


redis_manager = RedisManager()
