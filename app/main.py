from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.cors import CORSMiddleware

from app.admin import AdminRegistration, authentication_backend
from app.api.v1.api import api_router
from app.core.redis import redis_manager
from app.core.config import settings
from fastapi.templating import Jinja2Templates

from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis
    await redis_manager.init_redis()
    yield
    # Shutdown: Close connection
    await redis_manager.close_redis()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

admin = Admin(app, engine, title=settings.PROJECT_NAME, authentication_backend=authentication_backend)


AdminRegistration(admin)

@app.get("/health")
def health():
    return {"status": "ok"}
