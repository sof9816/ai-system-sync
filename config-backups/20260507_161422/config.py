import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "GT AI Dashboard"
    DEBUG: bool = False
    
    # Paths
    AGENT_HOME: Path = Path("/Users/gt/Public/MyFiles/agent-home")
    HERMES_HOME: Path = Path.home() / ".hermes"
    OBSIDIAN_VAULT: Path = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault"
    
    # API - loaded from ~/.hermes/.env if available
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"
    KIMI_CODE_API_KEY: str = ""
    KIMI_CODE_BASE_URL: str = "https://api.kimi.com/coding"

    # Generic AI config (overrides KIMI_* when set via Models page)
    DASHBOARD_AI_PROVIDER: str = ""
    DASHBOARD_AI_MODEL: str = ""
    DASHBOARD_AI_BASE_URL: str = ""
    DASHBOARD_AI_API_KEY: str = ""
    
    # DB
    DATABASE_URL: str = f"sqlite:///{AGENT_HOME}/dashboard/data/dashboard.db"
    
    # Notifications
    NOTIFICATION_ENABLED: bool = True
    NOTIFICATION_BALANCE_THRESHOLD: float = 10.0  # dollars
    NOTIFICATION_DISK_THRESHOLD: float = 90.0     # percent
    
    model_config = SettingsConfigDict(
        env_file=str(Path.home() / ".hermes" / ".env"),
        extra="ignore",
    )

settings = Settings()
