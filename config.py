from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/gitex"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings():
    return Settings()
