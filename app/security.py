from __future__ import annotations

import hashlib
import secrets

from app import config


def hash_value(value: str) -> str:
    payload = f"{value}:{config.APP_SECRET}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)

