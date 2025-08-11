from pydantic import BaseModel, HttpUrl, field_validator

class MonitoringSettings(BaseModel):
    SENTRY_DSN: HttpUrl | None = None

    @field_validator("SENTRY_DSN", mode="before")
    @classmethod
    def _noneify(cls, v):
        if isinstance(v, str) and v.lower() in ("null", "none", ""):
            return None
        return v
