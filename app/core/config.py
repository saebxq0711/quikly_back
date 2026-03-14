from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    project_name: str
    environment: str = "local"
    database_url: str

    secret_key: str
    access_token_expire_minutes: int = 60

    cors_origins: str

    # --- Frontend ---
    frontend_url: str
    reset_token_expire_minutes: int = 30

    # --- SMTP ---
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str

    # --- SIIGO ---
    siigo_user: str
    siigo_key: str
    siigo_base_url: str

    # --- BANCOLOMBIA QR ---
    bancolombia_client_id: str
    bancolombia_client_secret: str
    bancolombia_merchant_id: str

    bancolombia_auth_url: str
    bancolombia_qr_url: str
    bancolombia_status_url: str

    bancolombia_public_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()