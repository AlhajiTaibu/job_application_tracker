import ssl
from redis.asyncio import Redis, ConnectionPool
from typing import Optional
from app.core.config import settings
from app.core.logging_config import logger


class RedisManager:
    def __init__(self) -> None:
        self.redis_host = settings.redis_host
        self.password = settings.redis_password
        self.redis_port = settings.redis_port
        self.redis_user = settings.redis_user

        # Keep track of both the pool and the client interface
        self.pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[Redis] = None

    async def init_redis(self):
        if self.pool is None:
            # Create an EXPLICIT connection pool. This is the fix.
            pool_kwargs = {
                "host": self.redis_host,
                "password": self.password,
                "port": self.redis_port,
                "username": self.redis_user,
                "db": 0,
                "decode_responses": True,
                "socket_connect_timeout": 15,
                "socket_timeout": 15,
                "socket_keepalive": True,
                "retry_on_timeout": True,
                "max_connections": 50,
                "health_check_interval": 30
            }

            # 2. Only inject SSL parameters if we are in Production
            if settings.is_prod:
                pool_kwargs["ssl"] = True
                pool_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
                logger.info("Configuring Redis Async Pool with SSL (Production).")
            else:
                logger.info("Configuring Redis Async Pool without SSL (Development).")

            # 3. Unpack the dictionary cleanly into the Pool constructor
            self.pool = ConnectionPool(**pool_kwargs)
            self.redis_client = Redis(connection_pool=self.pool)
            logger.info("Redis Async Connection Pool initialized successfully.")

        return self.redis_client

    async def close_redis(self):
        if self.redis_client:
            # Safely disconnect all active connections in the pool
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

    async def delete_key(self, key: str):
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as error:
            logger.error(f"Redis DELETE Error: {error}")


# Instantiate the singleton
redis_manager = RedisManager()