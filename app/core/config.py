from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    database_url: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    redis_host: str
    celery_broker_url: str
    celery_result_backend: str
    PROJECT_NAME: str = "Job Application Tracker"
    PROJECT_VERSION: str = "1.0.0"
    client_id: str
    client_secret: str
    redirect_uris: str
    project_id: str
    auth_uri: str
    token_uri: str
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()