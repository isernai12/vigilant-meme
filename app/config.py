from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Settings:
    app_name: str = "MCQ Practice Bot"
    base_url: str = "https://your-render-service.onrender.com"
    webhook_secret: str = "super-secret-webhook-token"
    bot_token: str = "PASTE_TELEGRAM_BOT_TOKEN_HERE"
    otp_secret: str = "replace-with-long-random-string"
    session_secret: str = "replace-with-session-secret"
    admin_telegram_ids: List[int] = field(default_factory=lambda: [123456789])
    database_url: str = (
        "postgresql://neko_cvdh_user:LRagi69HR0UdQWmXHO5TijgMfF1Sp0Ze@"
        "dpg-d5o6t0fgi27c73egfg1g-a.oregon-postgres.render.com/neko_cvdh"
    )
    session_days: int = 7
    otp_expiration_seconds: int = 120
    otp_resend_cooldown_seconds: int = 45
    otp_max_attempts: int = 5


settings = Settings()
