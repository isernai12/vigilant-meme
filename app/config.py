from __future__ import annotations

# Hardcoded configuration values. Replace placeholders with real values.

BOT_TOKEN = "TELEGRAM_BOT_TOKEN_HERE"
WEBHOOK_SECRET = "CHANGE_ME_WEBHOOK_SECRET"

LIBSQL_URL = "libsql://your-turso-instance.turso.io"
LIBSQL_AUTH_TOKEN = "YOUR_TURSO_AUTH_TOKEN"
LIBSQL_LOCAL_PATH = "data/local.db"

APP_SECRET = "CHANGE_ME_APP_SECRET_FOR_HASHING"

ADMIN_TELEGRAM_IDS = [123456789]

SESSION_COOKIE_NAME = "admin_session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
OTP_EXPIRY_SECONDS = 120
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 45

SERVER_BASE_URL = "https://your-render-domain.onrender.com"
