import warnings
from pydantic import BaseModel, model_validator
from typing_extensions import Self

class SecuritySettings(BaseModel):
    SECRET_KEY: str = "changethis"
    security: str = "changethis"
    FIRST_SUPERUSER: str = "changethis"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"

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