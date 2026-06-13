import ssl
from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from typing import Optional
from app.core.config import settings
from app.core.logging_config import logger


class RedisManager:
    def __init__(self) -> None:
        self.redis_host = settings.redis_host
        self.password = settings.redis_password
        self.redis_port = settings.redis_port
        self.redis_user = settings.redis_user

        self.pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[Redis] = None

    async def init_redis(self):
        if self.pool is None:
            protocol = "rediss" if settings.is_prod else "redis"

            redis_url = f"{protocol}://{self.redis_user}:{self.password}@{self.redis_host}:{self.redis_port}/0"

            pool_kwargs = {
                "decode_responses": True,
                "socket_connect_timeout": 15,
                "socket_timeout": 15,
                "socket_keepalive": True,
                "retry_on_timeout": True,
                "max_connections": 50,
                "health_check_interval": 30,
                "retry": Retry(ExponentialBackoff(cap=2, base=0.5), 3),
                "retry_on_error": [ConnectionError, TimeoutError],
            }

            if settings.is_prod:
                logger.info("Parsing Aiven production connection via secure SSL URL pool.")
                pool_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
            else:
                logger.info("Parsing local connection via unencrypted URL pool.")

            self.pool = ConnectionPool.from_url(redis_url, **pool_kwargs)
            self.redis_client = Redis(connection_pool=self.pool)
            logger.info("Redis Async URL Connection Pool initialized successfully.")

        return self.redis_client

    async def close_redis(self):
        if self.redis_client:
            await self.pool.disconnect()
            self.redis_client = None
            self.pool = None
            logger.info("Redis Async Connection Pool closed cleanly.")

    async def get_client(self) -> Redis:
        if self.redis_client is None:
            await self.init_redis()
        return self.redis_client

    async def set_value(self, key: str, value: str, expire_time: int = 3600):
        try:
            client = await self.get_client()
            await client.setex(key, expire_time, value)
        except Exception as error:
            logger.error(f"Redis SET Error: {error}")

    async def get_value(self, key: str) -> Optional[str]:
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as error:
            logger.error(f"Redis GET Error: {error}")
            return None

    async def delete_value(self, key: str):
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as error:
            logger.error(f"Redis DELETE Error: {error}")


redis_manager = RedisManager()