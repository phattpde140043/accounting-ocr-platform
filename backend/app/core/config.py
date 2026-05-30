from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACCOUNTING_OCR_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "Accounting OCR Platform"
    api_prefix: str = "/api/v1"
    environment: str = "local"
    auth_mode: str = "demo"
    database_url: str = "postgresql+asyncpg://accounting:accounting@localhost:5433/accounting_ocr"
    google_client_id: str = "demo-google-client-id"
    google_oauth_scope: str = "openid email profile"
    google_token_verifier_mode: str = "demo"
    openai_ocr_model: str = "gpt-4.1-mini"
    jwt_secret_key: str = "local-dev-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 60
    local_storage_root: str = "uploads"
    file_scanner_mode: str = "local-noop"
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, gt=0)

    @property
    def demo_auth_enabled(self) -> bool:
        return self.environment in {"local", "test"} and self.auth_mode == "demo"


settings = Settings()
