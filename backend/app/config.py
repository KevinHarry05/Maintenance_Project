from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./sbms.db"

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ALLOWED_ORIGINS: str = "localhost:3000"
    CORS_ORIGINS: str = ""  # Legacy, prefer CORS_ALLOWED_ORIGINS
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    COMPLAINT_UPLOAD_DIR: str = "uploads/complaints"
    GLOBAL_RATE_LIMIT_PER_MINUTE: int = 200
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    FCM_SERVER_KEY: str | None = None
    ENABLE_CELERY_HEALTH_CHECK: bool = False

    # Token Blacklist Configuration (Requirement 4)
    TOKEN_BLACKLIST_CLEANUP_HOUR: int = 2  # UTC hour for daily cleanup (0-23)
    TOKEN_BLACKLIST_CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # Email Verification Configuration (Requirement 5)
    EMAIL_VERIFICATION_ENABLED: bool = True
    VERIFICATION_TOKEN_EXPIRY_HOURS: int = 24
    RESEND_EMAIL_RATE_LIMIT: int = 3  # Max resend requests
    RESEND_EMAIL_RATE_LIMIT_WINDOW_MINUTES: int = 60

    # File Upload Configuration (Requirement 3)
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

    # Password Security Configuration (Requirement 8)
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_COMPLEXITY_REQUIRED: bool = True

    # Email Domain Configuration (Phase 3.1)
    DOMAIN: str | None = None

    # SMTP Configuration for Email
    SMTP_SERVER: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "SBMS"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        # Use new CORS_ALLOWED_ORIGINS if set, otherwise fall back to legacy CORS_ORIGINS
        origins_str = self.CORS_ALLOWED_ORIGINS or self.CORS_ORIGINS
        if not origins_str:
            return []
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


settings = Settings()