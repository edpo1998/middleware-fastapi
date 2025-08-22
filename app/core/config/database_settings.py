from pydantic import computed_field, BaseModel
from sqlalchemy.engine import URL

class DatabaseSettings(BaseModel):
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    ECHO_SQL:bool = False
    ASYNC_MODE:bool = True

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if bool(self.ASYNC_MODE) :
            return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB
            )
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB
        )
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI_STR(self) -> str:
        if bool(self.ASYNC_MODE) :
            return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB
            ).render_as_string(hide_password=False)
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB
        ).render_as_string(hide_password=False)