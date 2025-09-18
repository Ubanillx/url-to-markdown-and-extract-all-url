from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    应用配置类
    """
    app_name: str = "URL to Markdown and Extract URL"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()
