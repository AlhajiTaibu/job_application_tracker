import os
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = os.getenv("ENV_FILE", ".env.local")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Prevents crashing if .env has extra variables
    )
    secret_key: str
    algorithm: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    access_token_expire_minutes: int
    reset_password_token_expire_minutes: int
    refresh_token_expire_minutes: int
    redis_host: str
    celery_broker_url: str
    celery_result_backend: str
    PROJECT_NAME: str = "Job Application Tracker"
    PROJECT_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    client_id: str
    client_secret: str
    redirect_uris: str
    project_id: str
    auth_uri: str
    token_uri: str
    file_storage_project_id: str
    file_storage_secret_access_key: str
    file_storage_access_key_id: str
    file_storage_region_name: str
    max_file_size: int
settings = Settings()