"""Application Configuration module."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Portal Integration Settings
    portal_base_url: str = os.getenv("PORTAL_BASE_URL", "https://tnreginet.gov.in/portal")
    portal_timeout_seconds: float = float(os.getenv("PORTAL_TIMEOUT_SECONDS", "25.0"))
    portal_rate_limit_seconds: float = float(os.getenv("PORTAL_RATE_LIMIT_SECONDS", "2.0"))

    # Session Management Settings
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "900"))  # 15 minutes
    session_cleanup_interval_seconds: int = int(os.getenv("SESSION_CLEANUP_INTERVAL_SECONDS", "60"))

    # User-Agent for portal requests
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )


settings = Settings()

