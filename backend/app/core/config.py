from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Accounting OCR Platform"
    api_prefix: str = "/api/v1"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://accounting:accounting@localhost:5433/accounting_ocr"
    google_client_id: str = "demo-google-client-id"
    google_oauth_scope: str = "openid email profile"
    google_token_verifier_mode: str = "demo"
    openai_ocr_model: str = "gpt-4.1-mini"
    jwt_secret_key: str = "local-dev-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 60
    local_storage_root: str = "uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024


settings = Settings()
