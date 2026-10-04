from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "TikTok Shop Affiliate Trend Hunter"
    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = 8000
    
    # CORS origins
    cors_origins: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database
    database_url: str = "sqlite:///./affiliate.db"
    
    # TikTok Collector Settings
    tiktok_region: str = "VN"
    headless: bool = True
    max_concurrency: int = 2
    max_retries: int = 3
    request_timeout: int = 30
    request_delay_min: float = 1.0
    request_delay_max: float = 3.0
    
    # Scheduler Settings
    crawl_schedule: str = "08:00,12:00,16:00,20:00,00:00"
    tracked_products_per_run: int = Field(default=100, ge=1, le=1000)

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
