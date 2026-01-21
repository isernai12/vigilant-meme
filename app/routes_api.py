from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_otp,
    create_session,
    get_admin_from_session,
    get_or_create_admin,
    hash_otp_secret,
)
from app.config import settings
from app.db import get_session
from app.models import Admin, AdminOtp
from app.telegram_bot import bot, set_webhook

router = APIRouter(prefix="/api")


async def require_admin(request: Request, session: AsyncSession = Depends(get_session)) -> Admin:
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    admin = await get_admin_from_session(session, token)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return admin


@router.post("/auth/request-otp")
async def request_otp(payload: dict, session: AsyncSession = Depends(get_session)) -> JSONResponse:
    telegram_id = int(payload.get("telegram_id", 0))
    if telegram_id not in settings.admin_telegram_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    admin = await get_or_create_admin(session, telegram_id)
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin disabled")
    result = await session.execute(
        select(AdminOtp)
        .where(AdminOtp.admin_id == admin.id)
        .order_by(desc(AdminOtp.created_at))
        .limit(1)
    )
    last_otp = result.scalar_one_or_none()
    if last_otp:
        elapsed = (datetime.utcnow() - last_otp.created_at).total_seconds()
        if elapsed < settings.otp_resend_cooldown_seconds:
            raise HTTPException(status_code=429, detail="OTP recently sent")
    otp, code = await create_otp(session, admin)
    await bot.send_message(chat_id=telegram_id, text=f"Your login code is: {code}")
    return JSONResponse({"status": "sent", "expires_at": otp.expires_at.isoformat()})


@router.post("/auth/verify-otp")
async def verify_otp(payload: dict, response: Response, session: AsyncSession = Depends(get_session)) -> JSONResponse:
    telegram_id = int(payload.get("telegram_id", 0))
    code = str(payload.get("code", ""))
    if telegram_id not in settings.admin_telegram_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    result = await session.execute(
        select(AdminOtp)
        .where(AdminOtp.admin_id == admin.id)
        .order_by(desc(AdminOtp.created_at))
        .limit(1)
    )
    otp = result.scalar_one_or_none()
    if not otp:
        raise HTTPException(status_code=404, detail="OTP not found")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")
    if otp.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=400, detail="OTP attempts exceeded")
    if hash_otp_secret(code) != otp.code_hash:
        otp.attempts += 1
        await session.commit()
        raise HTTPException(status_code=400, detail="Invalid code")
    admin_session, raw_token = await create_session(session, admin)
    response.set_cookie(
        key="session_token",
        value=raw_token,
        httponly=True,
        secure=True,
        samesite="lax",
        expires=int(admin_session.expires_at.timestamp()),
    )
    return JSONResponse({"status": "verified"})


@router.post("/auth/logout")
async def logout(response: Response) -> JSONResponse:
    response.delete_cookie("session_token")
    return JSONResponse({"status": "logged_out"})


@router.post("/telegram/set-webhook")
async def admin_set_webhook(admin: Admin = Depends(require_admin)) -> JSONResponse:
    await set_webhook()
    return JSONResponse({"status": "webhook_set", "admin": admin.telegram_id})
