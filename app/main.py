from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.cors import CORSMiddleware

from app.admin import AdminRegistration, authentication_backend
from app.api.v1.api import api_router
from app.core.rate_limiting_middleware import SimpleRateLimitMiddleware
from app.core.redis import redis_manager
from app.core.config import settings
from fastapi.templating import Jinja2Templates

from app.database import engine
from sentry_sdk.integrations.fastapi import FastApiIntegration
from prometheus_fastapi_instrumentator import Instrumentator

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await redis_manager.init_redis()
    yield
    await app.state.redis.close()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.is_prod:
    app.add_middleware(
        SimpleRateLimitMiddleware,
        exclude_paths=["/docs", "/redoc", "/openapi.json"],
        limit=settings.rate_limiter_limit,  # Allow 100 requests
        window=60,  # Per minute
    )

app.include_router(api_router, prefix="/api/v1")

admin = Admin(app, engine, title=settings.PROJECT_NAME, authentication_backend=authentication_backend)


AdminRegistration(admin)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.get("/")
def root():
    return {"status": "ok", "app": "Job Tracker API"}

@app.get("/health")
def health():
    return {"status": "ok"}
