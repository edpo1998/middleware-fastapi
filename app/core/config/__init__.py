# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from .app_settings      import AppSettings
from .database_settings import DatabaseSettings
from .email_settings    import EmailSettings
from .security_settings import SecuritySettings
from .cors_settings     import CorsSettings
from .monitoring_settings import MonitoringSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )
    app:        AppSettings
    db:         DatabaseSettings
    email:      EmailSettings
    security:   SecuritySettings
    cors:       CorsSettings
    monitoring: MonitoringSettings

settings = Settings()
