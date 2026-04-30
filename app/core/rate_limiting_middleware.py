import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging_config import logger


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int, window: int, exclude_paths: list = None):
        super().__init__(app)
        self.redis = Redis(
            host=settings.redis_host,
            password=settings.redis_password,
            port=6379,
            db=0,
            socket_timeout=5,
            retry_on_timeout=True,
            ssl=True if settings.is_prod else False,
            decode_responses=True if settings.is_prod else False,
            max_connections=20
        )
        self.limit = limit
        self.window = window
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health", "/admin"]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        # --- IDEMPOTENCY LOGIC ---
        # Only apply to "Write" operations
        # if request.method in ["POST", "PUT", "PATCH"]:
        #     ikey = request.headers.get("X-Idempotency-Key")
        #     if ikey:
        #         redis_key = f"idempotency:{ikey}"
        #         # Set key for 24 hours only if it doesn't exist
        #         is_new = await self.redis.set(redis_key, "locked", ex=86400, nx=True)
        #
        #         if not is_new:
        #             return JSONResponse(
        #                 status_code=status.HTTP_409_CONFLICT,
        #                 content={"detail": "Request already processed or in progress."}
        #             )
        client_ip = request.client.host
        window_id = int(time.time() // self.window)
        key = f"rate_limit:{client_ip}:{window_id}"

        try:
            current_count = await self.redis.incr(key)
            if current_count == 1:
                await self.redis.expire(key, self.window)

            if current_count > self.limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests."},
                )
        except Exception as e:
            logger.error(f"Redis Error: {e}")
        return await call_next(request)