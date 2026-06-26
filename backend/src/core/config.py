import os


class Settings:
    app_name: str = os.getenv("APP_NAME", "ModelGate Agent Studio API")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./modelgate.db")
    api_v1_prefix: str = "/api/v1"


settings = Settings()
