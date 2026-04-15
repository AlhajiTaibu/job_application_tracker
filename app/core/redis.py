from redis.asyncio import Redis
from typing import Optional
from app.core.config import settings


class RedisManager:
    def __init__(self) -> None:
        self.redis_host = settings.redis_host
        self.redis_client: Optional[Redis] = None

    async def init_redis(self) -> None:
        self.redis_client = Redis(
            host=self.redis_host,
            port=6379,
            db=1,
            decode_responses=False,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=20
        )

    async def close_redis(self):
        """Cleanly close the pool."""
        if self.redis_client:
            await self.redis_client.aclose()

redis_manager = RedisManager()