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
        self.redis_client = Redis(
            host=self.redis_host,
            password=self.password,
            port=self.redis_port,
            username=self.redis_user,
            db=1,
            decode_responses=True if settings.is_prod else False,
            socket_timeout=5,
            retry_on_timeout=True,
            ssl=True if settings.is_prod else False,
            max_connections=20
        )
        return self.redis_client
    async def close_redis(self):
        """Cleanly close the pool."""
        if self.redis_client:
            await self.redis_client.aclose()

    async def get_client(self):
        if self.redis_client:
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
            value = await client.get(key)
            return value
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