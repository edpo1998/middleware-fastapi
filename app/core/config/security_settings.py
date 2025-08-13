import warnings
from pydantic import BaseModel, model_validator
from typing_extensions import Self

class SecuritySettings(BaseModel):
    SECRET_KEY: str = "changethis"
    security: str = "changethis"
    FIRST_SUPERUSER: str = "changethis"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"

    ENABLE_HMAC: bool = False
    HMAC_WINDOW_SECONDS: int = 300
    ENABLE_TIMESTAMP: bool = False
    REQUIRE_TIMESTAMP_WITH_NONCE: bool = False      
    ENABLE_NONCE: bool = False
    USE_REDIS_FOR_NONCE: bool = False
    REDIS_DSN: str | None = None
    ENABLE_IDEMPOTENCY: bool = False
    IDEMPOTENCY_REQUIRED: bool = False
    IDEMPOTENCY_TTL_DAYS: int = 14   
    TRUST_PROXY_HEADERS: bool = False
    

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it before deployment."
            )
            warnings.warn(message, stacklevel=1)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD)
        return self