from __future__ import annotations

import time
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import config
from app import db
from app import security
from app import telegram_api
from app.admin_pages import (
    dashboard_page,
    login_page,
    new_question_page,
    questions_list_page,
    verify_page,
)

router = APIRouter()


def get_session_hash(request: Request) -> str | None:
    return request.cookies.get(config.SESSION_COOKIE_NAME)


def require_admin(request: Request) -> int | None:
    session_hash = get_session_hash(request)
    if not session_hash:
        return None
    now = int(time.time())
    rows = db.exec_read(
        """
        SELECT telegram_id FROM admin_sessions
        WHERE session_hash = ? AND expires_at >= ?
        """,
        (session_hash, now),
    )
    if not rows:
        return None
    return int(rows[0][0])


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login() -> str:
    return login_page()


@router.post("/admin/request-otp", response_class=HTMLResponse)
async def request_otp(telegram_id: int = Form(...)) -> str:
    if telegram_id not in config.ADMIN_TELEGRAM_IDS:
        return login_page("Not allowed.")

    now = int(time.time())
    last_rows = db.exec_read(
        """
        SELECT created_at FROM admin_otps
        WHERE telegram_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    if last_rows and now - int(last_rows[0][0]) < config.OTP_RESEND_COOLDOWN_SECONDS:
        return login_page("Please wait before requesting another code.")

    otp = security.generate_otp()
    otp_hash = security.hash_value(otp)
    expires_at = now + config.OTP_EXPIRY_SECONDS
    db.exec_write(
        """
        INSERT INTO admin_otps (telegram_id, code_hash, expires_at, attempts, created_at)
        VALUES (?, ?, ?, 0, ?)
        """,
        (telegram_id, otp_hash, expires_at, now),
    )
    await telegram_api.send_message(
        telegram_id,
        f"Your admin login code is: {otp} (valid for {config.OTP_EXPIRY_SECONDS} sec)",
    )
    return verify_page(telegram_id, "Code sent. Check Telegram.")


@router.post("/admin/verify-otp")
async def verify_otp(telegram_id: int = Form(...), code: str = Form(...)) -> RedirectResponse | HTMLResponse:
    now = int(time.time())
    rows = db.exec_read(
        """
        SELECT id, code_hash, expires_at, attempts FROM admin_otps
        WHERE telegram_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    if not rows:
        return verify_page(telegram_id, "No OTP found. Please request again.")

    otp_id, code_hash, expires_at, attempts = rows[0]
    if now > int(expires_at):
        return verify_page(telegram_id, "OTP expired. Request a new one.")
    if int(attempts) >= config.OTP_MAX_ATTEMPTS:
        return verify_page(telegram_id, "Too many attempts. Request a new code.")

    if security.hash_value(code.strip()) != code_hash:
        db.exec_write(
            "UPDATE admin_otps SET attempts = attempts + 1 WHERE id = ?",
            (otp_id,),
        )
        return verify_page(telegram_id, "Invalid code.")

    session_token = security.generate_session_token()
    session_hash = security.hash_value(session_token)
    expires_at = now + config.SESSION_MAX_AGE_SECONDS
    db.exec_write(
        """
        INSERT INTO admin_sessions (telegram_id, session_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (telegram_id, session_hash, expires_at, now),
    )

    response = RedirectResponse(url="/admin", status_code=302)
    response.set_cookie(
        config.SESSION_COOKIE_NAME,
        session_hash,
        max_age=config.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    if not require_admin(request):
        return RedirectResponse("/admin/login", status_code=302)
    return HTMLResponse(dashboard_page())


@router.post("/admin/logout")
async def admin_logout(request: Request) -> RedirectResponse:
    session_hash = get_session_hash(request)
    if session_hash:
        db.exec_write("DELETE FROM admin_sessions WHERE session_hash = ?", (session_hash,))
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie(config.SESSION_COOKIE_NAME)
    return response


@router.get("/admin/questions/new", response_class=HTMLResponse)
async def new_question(request: Request) -> HTMLResponse | RedirectResponse:
    if not require_admin(request):
        return RedirectResponse("/admin/login", status_code=302)
    return HTMLResponse(new_question_page())


@router.post("/admin/questions/new", response_class=HTMLResponse)
async def create_question(
    request: Request,
    topic: str = Form("") ,
    question: str = Form(...),
    a: str = Form(...),
    b: str = Form(...),
    c: str = Form(...),
    d: str = Form(...),
    correct: str = Form(...),
    explanation: str = Form(""),
) -> HTMLResponse | RedirectResponse:
    if not require_admin(request):
        return RedirectResponse("/admin/login", status_code=302)
    now = int(time.time())
    db.exec_write(
        """
        INSERT INTO questions (topic, question, a, b, c, d, correct, explanation, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            topic.strip() or None,
            question.strip(),
            a.strip(),
            b.strip(),
            c.strip(),
            d.strip(),
            correct.strip().upper(),
            explanation.strip() or None,
            now,
        ),
    )
    return HTMLResponse(new_question_page("Question saved!"))


@router.get("/admin/questions", response_class=HTMLResponse)
async def list_questions(request: Request) -> HTMLResponse | RedirectResponse:
    if not require_admin(request):
        return RedirectResponse("/admin/login", status_code=302)
    rows = db.exec_read(
        """
        SELECT id, topic, question, correct, created_at
        FROM questions
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    return HTMLResponse(questions_list_page(rows))

