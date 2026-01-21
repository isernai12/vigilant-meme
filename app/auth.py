from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Admin, AdminOtp, AdminSession


def hash_code(raw_code: str) -> str:
    return bcrypt.hash(raw_code)


def verify_code(raw_code: str, code_hash: str) -> bool:
    return bcrypt.verify(raw_code, code_hash)


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(f"{settings.session_secret}{raw_token}".encode()).hexdigest()


def hash_otp_secret(raw_code: str) -> str:
    return hashlib.sha256(f"{settings.otp_secret}{raw_code}".encode()).hexdigest()


def otp_expiration() -> datetime:
    return datetime.utcnow() + timedelta(seconds=settings.otp_expiration_seconds)


def session_expiration() -> datetime:
    return datetime.utcnow() + timedelta(days=settings.session_days)


async def get_or_create_admin(session: AsyncSession, telegram_id: int) -> Admin:
    result = await session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
    admin = result.scalar_one_or_none()
    if admin:
        return admin
    admin = Admin(telegram_id=telegram_id, is_active=True)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def create_otp(session: AsyncSession, admin: Admin) -> tuple[AdminOtp, str]:
    code = generate_otp_code()
    code_hash = hash_otp_secret(code)
    otp = AdminOtp(
        admin_id=admin.id,
        code_hash=code_hash,
        expires_at=otp_expiration(),
    )
    session.add(otp)
    await session.commit()
    await session.refresh(otp)
    return otp, code


async def create_session(session: AsyncSession, admin: Admin) -> tuple[AdminSession, str]:
    raw_token = secrets.token_urlsafe(32)
    session_hash = hash_session_token(raw_token)
    admin_session = AdminSession(
        admin_id=admin.id,
        session_hash=session_hash,
        expires_at=session_expiration(),
    )
    session.add(admin_session)
    await session.commit()
    await session.refresh(admin_session)
    return admin_session, raw_token


async def get_admin_from_session(session: AsyncSession, raw_token: str) -> Admin | None:
    session_hash = hash_session_token(raw_token)
    result = await session.execute(
        select(AdminSession).where(AdminSession.session_hash == session_hash)
    )
    admin_session = result.scalar_one_or_none()
    if not admin_session:
        return None
    if admin_session.expires_at < datetime.utcnow():
        return None
    return admin_session.admin
