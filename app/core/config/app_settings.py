from pydantic import BaseModel
class AppSettings(BaseModel):
    PROJECT_NAME: str = "Logistaas-Middleware"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "local"
    FRONTEND_HOST: str = "http://localhost:5173"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 60