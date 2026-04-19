from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    @property
    def is_prod(self) -> bool:
        return self.env == "production"

    database_url: str
    db_echo: bool = False

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str | None = None
    access_token_expire_minutes: int = 15

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    ws_auth_token: str | None = None

    groq_api_key: str | None = None


settings = Settings()