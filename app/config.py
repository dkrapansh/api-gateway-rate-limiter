from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    max_requests: int = 5
    window_seconds: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()